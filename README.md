# 🧪 BANK Open Source Tests

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Pytest](https://img.shields.io/badge/Pytest-testing-green?logo=pytest)
![Allure](https://img.shields.io/badge/Allure-Reports-orange)
![CI](https://img.shields.io/badge/Jenkins-CI-D24939?logo=jenkins)

This repository contains **automation tests for the BANK open-source testing platform**.

The goal of this project is to provide **real API automation examples** using:

- Pytest
- Allure reports
- REST API testing
- CI pipelines (Jenkins)

The project can be used for **learning QA Automation and API testing**.

---

# 🏦 BANK Platform

Tests are written for the **BANK testing platform**.

Repository:

https://github.com/danilfg/bank-open-source

The platform simulates a **banking system for QA engineers**, where you can practice:

- API testing
- automation testing
- CI/CD pipelines
- working with databases
- distributed systems

---

# 🚀 Quick Start

Clone the repository:

```bash
git clone https://github.com/danilfg/bank-open-source-tests.git
cd bank-open-source-tests
````

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

To generate Allure reports locally:

```bash
pytest --alluredir=allure-results
allure serve allure-results
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

Example:

```
tests/
   test_api.py
   test_auth.py
   test_students.py
```

3️⃣ Push the changes to **your own public repository**

4️⃣ Run the tests in CI using **Jenkins + Allure**

---

# ⚙️ Running Your Tests in Jenkins

You can run your own tests using Jenkins.

Steps:

1️⃣ Fork or clone this repository.

2️⃣ Add your tests.

3️⃣ Create a **public GitHub repository** with your tests.

4️⃣ In Jenkins:

Replace the repository URL with your own repository.

Example:

```
https://github.com/YOUR_USERNAME/bank-open-source-tests
```

5️⃣ Run the pipeline.

Jenkins will:

* clone your repository
* run tests with Pytest
* generate **Allure reports**

---

# 📚 Learning Goals

This repository helps QA engineers practice:

* writing API tests
* structuring test projects
* running tests in CI
* generating Allure reports

---

# 📜 License

This project is distributed under the **MIT License**.
