# DevOps Capstone: Customer Accounts Service

[![Build Status](https://github.com/shyrradev/devops-capstone-project/actions/workflows/ci-build.yaml/badge.svg)](https://github.com/shyrradev/devops-capstone-project/actions/workflows/ci-build.yaml)

A REST API for managing customer accounts, developed with Flask, SQLAlchemy, and test driven development. Based on the IBM Developer Skills Network DevOps capstone starter.

## API

| Method | Endpoint | Result |
|---|---|---|
| POST | /accounts | Create an account (201) |
| GET | /accounts | List accounts (200) |
| GET | /accounts/{id} | Read account (200 or 404) |
| PUT | /accounts/{id} | Update account (200 or 404) |
| DELETE | /accounts/{id} | Delete account (204) |
| GET | /health | Health check (200) |

Accounts include name, email, address, optional phone_number, and date_joined.

## Development

Use Python 3.9 and PostgreSQL. Set DATABASE_URI to your PostgreSQL connection string, install requirements.txt, and run `nosetests`. Tests require a dedicated database because they clear account records between cases.

```sh
pip install -r requirements.txt
nosetests
flake8 service tests
```

The GitHub workflow runs lint and unit tests. The Docker image exposes port 8080. Kubernetes manifests and Tekton delivery tasks are maintained with the source.

## Planning

User stories and sprint estimates are tracked in this repository's linked GitHub project. The user-story template documents role, capability, benefit, and acceptance criteria.

Original starter: https://github.com/ibm-developer-skills-network/aolwx-devops-capstone-template
