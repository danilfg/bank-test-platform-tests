# 🧪 BANK Open Source Tests

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Pytest](https://img.shields.io/badge/Pytest-testing-green?logo=pytest)
![Allure](https://img.shields.io/badge/Allure-Reports-orange)
![Jenkins](https://img.shields.io/badge/Jenkins-CI-D24939?logo=jenkins)

This repository contains **automation tests for the BANK open-source testing platform**.

The goal of this project is to provide **real examples of API automation tests** using:

* Pytest
* REST API testing
* Allure reports
* CI pipelines (Jenkins)

This repository can be used to **practice QA Automation and API testing**.

---

# 🏦 BANK Platform

Tests are written for the **BANK testing platform**.

Platform repository:

[https://github.com/danilfg/bank-open-source](https://github.com/danilfg/bank-open-source)

The platform simulates a **banking system for QA engineers**, where you can practice:

* API testing
* automation testing
* CI/CD pipelines
* working with databases
* distributed systems

---

# ⚠️ Requirements

Tests require the **BANK platform to be running locally**.

First clone and start the platform:

```bash
git clone https://github.com/danilfg/bank-open-source.git
cd bank-open-source
docker compose up
```

If the platform is not running, the tests will fail because the API will not be available.

API base URL used in tests:

```
http://127.0.0.1:8080
```

---

# 🚀 Quick Start

Clone the repository:

```bash
git clone https://github.com/danilfg/bank-open-source-tests.git
cd bank-open-source-tests
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

---

# 📊 Allure Reports

Tests support **Allure reporting**.

To generate a report locally:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

Allure will start a local server and open the report in your browser.

---

# ⚙️ Install Allure

Before running the report you must install **Allure CLI**.

---

## 🪟 Windows

Install via **Scoop** (recommended):

```powershell
scoop install allure
```

If Scoop is not installed:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
scoop install allure
```

---

## 🍎 macOS

Install using **Homebrew**:

```bash
brew install allure
```

---

## 🐧 Ubuntu / Linux

Install Java first:

```bash
sudo apt update
sudo apt install openjdk-11-jre
```

Then install Allure:

```bash
sudo apt install allure
```

If the package is not available, install manually:

```bash
wget https://github.com/allure-framework/allure2/releases/latest/download/allure-2.27.0.tgz
tar -zxvf allure-2.27.0.tgz
sudo mv allure-2.27.0 /opt/allure
sudo ln -s /opt/allure/bin/allure /usr/bin/allure
```

---

## ✅ Verify Installation

Check that Allure is installed:

```bash
allure --version
```

---

## 🚀 Run Report

After installation:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```
---

# 🧪 Example Test

Example Pytest test demonstrating a **full employee lifecycle**:

create → update → delete.

```python
import requests

BASE_URL = "http://127.0.0.1:8080"

EMAIL = "student@easyitlab.tech"
PASSWORD = "student123"


def get_token():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": EMAIL,
            "password": PASSWORD
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_create_update_delete_employee():

    token = get_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # CREATE employee
    create_response = requests.post(
        f"{BASE_URL}/students/employees",
        json={
            "email": "employee.demo@demobank.local",
            "full_name": "Demo Employee"
        },
        headers=headers
    )

    assert create_response.status_code == 201

    employee_id = create_response.json()["id"]

    # UPDATE employee
    update_response = requests.patch(
        f"{BASE_URL}/students/employees/{employee_id}",
        json={
            "full_name": "Updated Demo Employee"
        },
        headers=headers
    )

    assert update_response.status_code == 200

    # DELETE employee
    delete_response = requests.delete(
        f"{BASE_URL}/students/employees/{employee_id}",
        headers=headers
    )

    assert delete_response.status_code == 204
```

---

# 🧑‍💻 Contributing

You can use this repository to **practice writing automation tests**.

Typical workflow:

1️⃣ Clone the repository

```bash
git clone https://github.com/danilfg/bank-open-source-tests.git
```

2️⃣ Add your own tests

Example structure:

```
tests/
   test_auth.py
   test_employees.py
   test_clients.py
```

3️⃣ Push tests to **your own public GitHub repository**

---

# ⚙️ Running Your Tests in Jenkins

You can run your own tests in Jenkins with **Allure reports**.

Steps:

1️⃣ Fork or clone this repository.

2️⃣ Add your own tests.

3️⃣ Create your own **public GitHub repository**.

4️⃣ In Jenkins replace the repository URL with your repository.

Example:

```
https://github.com/YOUR_USERNAME/bank-open-source-tests
```

5️⃣ Run the Jenkins pipeline.

Jenkins will:

* clone your repository
* install dependencies
* run Pytest
* generate **Allure reports**

---

# 📚 Learning Goals

This repository helps QA engineers practice:

* API automation testing
* structuring test frameworks
* CI/CD pipelines
* Allure reporting
* working with real APIs

---

# 📜 License

This project is distributed under the **MIT License**.
