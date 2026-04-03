from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Iterator
from typing import Any

import allure
import pytest
import requests


STUDENT_EMAIL = os.getenv("TEST_STUDENT_EMAIL", "student@easyitlab.tech")
STUDENT_PASSWORD = os.getenv("TEST_STUDENT_PASSWORD", "student123")
HTTP_TIMEOUT = float(os.getenv("TEST_HTTP_TIMEOUT", "20"))


def _attach_json(name: str, payload: Any) -> None:
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def _resolve_base_url() -> str:
    candidates: list[str] = []
    explicit = os.getenv("TEST_API_BASE_URL")
    if explicit:
        candidates.append(explicit.rstrip("/"))
    candidates.extend(["http://127.0.0.1:8080", "http://api-gateway:8080"])
    for candidate in candidates:
        try:
            response = requests.get(f"{candidate}/health", timeout=5)
        except requests.RequestException:
            continue
        if response.status_code < 500:
            return candidate
    pytest.fail(f"API base URL was not resolved. Tried: {candidates}")


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def api_request(session_client: requests.Session, method: str, path: str, **kwargs: Any) -> requests.Response:
    base_url = getattr(session_client, "base_url", "")
    kwargs.setdefault("timeout", HTTP_TIMEOUT)
    kwargs.setdefault("allow_redirects", True)
    return session_client.request(method=method, url=f"{base_url}{path}", **kwargs)


def login_student(
    session_client: requests.Session,
    email: str = STUDENT_EMAIL,
    password: str = STUDENT_PASSWORD,
) -> requests.Response:
    return api_request(session_client, "POST", "/auth/login", json={"email": email, "password": password})


def login_student_with_retry(
    session_client: requests.Session,
    email: str = STUDENT_EMAIL,
    password: str = STUDENT_PASSWORD,
    attempts: int = 4,
) -> requests.Response:
    response: requests.Response | None = None
    for _ in range(attempts):
        response = login_student(session_client, email=email, password=password)
        if response.status_code != 429:
            return response
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            sleep_for = float(retry_after) + 1.0
        else:
            match = re.search(r"/(\d+)s", response.text)
            sleep_for = float(match.group(1)) + 1.0 if match else 61.0
        time.sleep(min(max(sleep_for, 5.0), 90.0))
    assert response is not None
    return response


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return _resolve_base_url()


@pytest.fixture(scope="session")
def session_client(api_base_url: str) -> Iterator[requests.Session]:
    with requests.Session() as client:
        client.base_url = api_base_url  # type: ignore[attr-defined]
        yield client


@pytest.fixture(scope="session")
def student_auth(session_client: requests.Session) -> dict[str, Any]:
    response = login_student_with_retry(session_client)
    if response.status_code != 200:
        pytest.fail(f"Cannot authenticate student for test session. status={response.status_code}, body={response.text}")
    body = response.json()
    return {"access_token": body["access_token"], "refresh_token": body["refresh_token"]}


@pytest.fixture(scope="session")
def refreshed_auth(session_client: requests.Session, student_auth: dict[str, Any]) -> dict[str, Any]:
    response = api_request(session_client, "POST", "/auth/refresh", json={"refresh_token": student_auth["refresh_token"]})
    if response.status_code != 200:
        pytest.fail(f"Cannot refresh student token for test session. status={response.status_code}, body={response.text}")
    return response.json()


@pytest.fixture(scope="session")
def seeded_entities(session_client: requests.Session, student_auth: dict[str, Any]) -> dict[str, Any]:
    response = api_request(
        session_client,
        "POST",
        "/students/entities/generate",
        json={"confirm_cleanup": True},
        headers=auth_headers(student_auth["access_token"]),
    )
    if response.status_code != 200:
        pytest.fail(f"Cannot seed student entities. status={response.status_code}, body={response.text}")
    return response.json()


@allure.epic("Student Platform")
@allure.feature("Auth Service")
@pytest.mark.auth
@pytest.mark.rest_api
@pytest.mark.parametrize(
    ("email", "password", "expected_status"),
    [
        pytest.param("student@easyitlab.tech", "student123", 200, id="valid-student-credentials"),
        pytest.param("student@easyitlab.tech", "wrong-password", 401, id="invalid-password"),
    ],
)
def test_auth_login_matrix(session_client: requests.Session, email: str, password: str, expected_status: int) -> None:
    with allure.step("Precondition: prepare login payload for auth service"):
        payload = {"email": email, "password": password}
        _attach_json("login-payload", payload)

    with allure.step("Action: send POST /auth/login"):
        response = login_student_with_retry(session_client, email=email, password=password)
        _attach_json("login-response", response.json())

    with allure.step("Postcondition: status code and contract must match scenario"):
        assert response.status_code == expected_status
        if expected_status == 200:
            body = response.json()
            assert body["access_token"]
            assert body["refresh_token"]
            assert body["token_type"] == "bearer"
            assert body["expires_in"] > 0


@allure.epic("Student Platform")
@allure.feature("Auth Service")
@pytest.mark.auth
@pytest.mark.parametrize(
    ("field_name", "expected_value"),
    [
        pytest.param("email", STUDENT_EMAIL, id="email"),
        pytest.param("system_role", "STUDENT", id="system-role"),
        pytest.param("full_name", "Student User", id="full-name"),
    ],
)
def test_auth_me_profile_required_fields(
    session_client: requests.Session,
    student_auth: dict[str, Any],
    field_name: str,
    expected_value: str,
) -> None:
    with allure.step("Precondition: student session token is prepared"):
        access_token = student_auth["access_token"]

    with allure.step("Action: send GET /auth/me"):
        response = api_request(session_client, "GET", "/auth/me", headers=auth_headers(access_token))
        _attach_json("auth-me-response", response.json())

    with allure.step("Postcondition: selected field must be present and valid"):
        assert response.status_code == 200
        profile = response.json()
        assert profile[field_name] == expected_value


@allure.epic("Student Platform")
@allure.feature("Auth Service")
@pytest.mark.auth
@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("access_token", id="access-token"),
        pytest.param("refresh_token", id="refresh-token"),
        pytest.param("token_type", id="token-type"),
    ],
)
def test_auth_refresh_contract(refreshed_auth: dict[str, Any], field_name: str) -> None:
    with allure.step("Precondition: refresh response payload is prepared"):
        _attach_json("refresh-response", refreshed_auth)

    with allure.step("Action: read selected field from refresh payload"):
        value = refreshed_auth.get(field_name)

    with allure.step("Postcondition: selected field exists and is non-empty"):
        assert value


@allure.epic("Student Platform")
@allure.feature("Dashboard Service")
@pytest.mark.dashboard
@pytest.mark.parametrize(
    "metric_name",
    [
        pytest.param("employees_total", id="employees-total"),
        pytest.param("employees_active", id="employees-active"),
        pytest.param("clients_total", id="clients-total"),
        pytest.param("accounts_total", id="accounts-total"),
        pytest.param("tickets_total", id="tickets-total"),
    ],
)
def test_dashboard_non_negative_metrics(
    session_client: requests.Session,
    student_auth: dict[str, Any],
    metric_name: str,
) -> None:
    with allure.step("Precondition: student session token is prepared"):
        access_token = student_auth["access_token"]

    with allure.step("Action: send GET /students/dashboard"):
        response = api_request(session_client, "GET", "/students/dashboard", headers=auth_headers(access_token))
        _attach_json("dashboard-response", response.json())

    with allure.step("Postcondition: selected metric must be integer and non-negative"):
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload[metric_name], int)
        assert payload[metric_name] >= 0


@allure.epic("Student Platform")
@allure.feature("Tools Access")
@pytest.mark.parametrize(
    ("service_name", "expected_title", "expected_url_prefix"),
    [
        pytest.param("JENKINS", "Jenkins", "http://", marks=[pytest.mark.jenkins], id="jenkins-tool"),
        pytest.param("ALLURE", "Allure", "http://", marks=[pytest.mark.allure], id="allure-tool"),
        pytest.param("POSTGRES", "PostgreSQL", None, marks=[pytest.mark.postgres], id="postgres-tool"),
        pytest.param("REST_API", "REST API / Swagger", "/students/docs", marks=[pytest.mark.rest_api], id="rest-api-tool"),
    ],
)
def test_tools_access_cards_per_service(
    session_client: requests.Session,
    student_auth: dict[str, Any],
    service_name: str,
    expected_title: str,
    expected_url_prefix: str | None,
) -> None:
    with allure.step("Precondition: student session token is prepared"):
        access_token = student_auth["access_token"]

    with allure.step(f"Action: send GET /students/tools/{service_name}"):
        response = api_request(session_client, "GET", f"/students/tools/{service_name}", headers=auth_headers(access_token))
        _attach_json(f"tool-{service_name.lower()}-response", response.json())

    with allure.step("Postcondition: service card must be active and correctly resolved"):
        assert response.status_code == 200
        payload = response.json()
        assert payload["service_name"] == service_name
        assert payload["title"] == expected_title
        assert payload["status"] == "ACTIVE"
        assert payload["principal"] == STUDENT_EMAIL
        if expected_url_prefix is None:
            assert payload["url"] is None
        else:
            assert str(payload["url"]).startswith(expected_url_prefix)


@allure.epic("Student Platform")
@allure.feature("Entities Generate")
@pytest.mark.employees
@pytest.mark.clients
@pytest.mark.rest_api
@pytest.mark.parametrize(
    ("min_employees", "min_clients"),
    [
        pytest.param(1, 1, id="minimum-entities"),
    ],
)
def test_entities_generate_payload_contract(
    seeded_entities: dict[str, Any],
    min_employees: int,
    min_clients: int,
) -> None:
    with allure.step("Precondition: entities were generated by fixture"):
        _attach_json("seeded-entities", seeded_entities)

    with allure.step("Action: use generation payload from fixture"):
        payload = seeded_entities

    with allure.step("Postcondition: payload contains expected counts and IDs"):
        assert payload["run_id"]
        assert payload["created_employees"] >= min_employees
        assert payload["created_clients"] >= min_clients
        assert len(payload["employee_ids"]) == payload["created_employees"]
        assert len(payload["client_ids"]) == payload["created_clients"]


@allure.epic("Student Platform")
@allure.feature("Employees Service")
@pytest.mark.employees
@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("id", id="id"),
        pytest.param("email", id="email"),
        pytest.param("username", id="username"),
        pytest.param("status", id="status"),
    ],
)
def test_employees_list_required_fields(
    session_client: requests.Session,
    student_auth: dict[str, Any],
    seeded_entities: dict[str, Any],
    field_name: str,
) -> None:
    with allure.step("Precondition: student data is seeded and token is ready"):
        assert seeded_entities["created_employees"] > 0
        access_token = student_auth["access_token"]

    with allure.step("Action: send GET /students/employees"):
        response = api_request(session_client, "GET", "/students/employees", headers=auth_headers(access_token))
        _attach_json("employees-response", response.json())

    with allure.step("Postcondition: every employee row has selected required field"):
        assert response.status_code == 200
        rows = response.json()
        assert isinstance(rows, list)
        assert len(rows) >= 1
        for row in rows:
            assert row.get(field_name) is not None


@allure.epic("Student Platform")
@allure.feature("Clients Service")
@pytest.mark.clients
@pytest.mark.parametrize(
    "status_filter",
    [
        pytest.param(None, id="all-statuses"),
        pytest.param("ACTIVE", id="active"),
        pytest.param("BLOCKED", id="blocked"),
        pytest.param("SUSPENDED", id="suspended"),
    ],
)
def test_clients_status_filter(
    session_client: requests.Session,
    student_auth: dict[str, Any],
    seeded_entities: dict[str, Any],
    status_filter: str | None,
) -> None:
    with allure.step("Precondition: student data is seeded and token is ready"):
        assert seeded_entities["created_clients"] > 0
        access_token = student_auth["access_token"]

    with allure.step("Action: send GET /students/clients with optional status filter"):
        params = {"status": status_filter} if status_filter else None
        response = api_request(session_client, "GET", "/students/clients", params=params, headers=auth_headers(access_token))
        _attach_json("clients-response", response.json())

    with allure.step("Postcondition: if status filter is set, all rows match requested status"):
        assert response.status_code == 200
        rows = response.json()
        assert isinstance(rows, list)
        if status_filter:
            assert all(item["status"] == status_filter for item in rows)


@allure.epic("Student Platform")
@allure.feature("Jenkins Service")
@pytest.mark.jenkins
@pytest.mark.parametrize(
    "run_field",
    [
        pytest.param("build_number", id="build-number"),
        pytest.param("status", id="status"),
        pytest.param("job_url", id="job-url"),
        pytest.param("allure_url", id="allure-url"),
    ],
)
def test_jenkins_runs_required_fields(
    session_client: requests.Session,
    student_auth: dict[str, Any],
    run_field: str,
) -> None:
    with allure.step("Precondition: student token is ready"):
        access_token = student_auth["access_token"]

    with allure.step("Action: trigger a Jenkins training run and request /students/jenkins/job/runs"):
        trigger_response = api_request(session_client, "POST", "/students/jenkins/job/run", headers=auth_headers(access_token))
        assert trigger_response.status_code == 200
        runs_response = api_request(session_client, "GET", "/students/jenkins/job/runs", headers=auth_headers(access_token))
        _attach_json("jenkins-runs-response", runs_response.json())

    with allure.step("Postcondition: latest run contains selected field"):
        assert runs_response.status_code == 200
        payload = runs_response.json()
        assert payload["service_name"] == "JENKINS"
        assert isinstance(payload["runs"], list)
        assert payload["runs"]
        assert payload["runs"][0].get(run_field) is not None


@allure.epic("Student Platform")
@allure.feature("Allure and REST API Entry")
@pytest.mark.parametrize(
    ("entry_name", "method", "path", "required_key"),
    [
        pytest.param("allure-open-url", "GET", "/students/allure/open-url", "url", marks=[pytest.mark.allure], id="allure-open-url"),
        pytest.param("docs-ticket", "POST", "/students/docs-ticket", "docs_url", marks=[pytest.mark.rest_api], id="rest-docs-ticket"),
    ],
)
def test_allure_and_docs_entrypoints(
    session_client: requests.Session,
    student_auth: dict[str, Any],
    entry_name: str,
    method: str,
    path: str,
    required_key: str,
) -> None:
    with allure.step("Precondition: student token is ready"):
        access_token = student_auth["access_token"]

    with allure.step(f"Action: call {method} {path}"):
        if method == "GET":
            response = api_request(session_client, "GET", path, headers=auth_headers(access_token))
        else:
            response = api_request(session_client, "POST", path, headers=auth_headers(access_token))
        _attach_json(f"{entry_name}-response", response.json())

    with allure.step("Postcondition: endpoint returns required navigation payload"):
        assert response.status_code == 200
        payload = response.json()
        assert payload.get(required_key)
        if path == "/students/allure/open-url":
            assert payload["mode"] in {"job", "report"}
        if path == "/students/docs-ticket":
            assert str(payload["docs_url"]).startswith("/students/docs?docs_ticket=")
