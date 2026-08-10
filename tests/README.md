# Test Strategy

This project now supports three test categories:

- `unit`: service-level behavior with mocked dependencies
- `api`: in-process Flask endpoint tests
- `contract`: deployed-service checks (microservice-ready)

## Folder Layout

Tests are organized by domain to keep files small and maintainable:

- `tests/user/`
- `tests/password/`
- `tests/role/`
- `tests/folder/`
- `tests/security_question/`
- `tests/audit_log/`
- `tests/contracts/`

Each domain folder follows this pattern:

- `test_service.py` for business/service logic
- `test_endpoints.py` for Flask route/controller behavior
- `test_data.py` for shared mocks and fixture builders

Password history currently lives at `tests/password/test_history.py`.

## Useful Commands

Run everything:

```powershell
python -m pytest
```

Run only unit tests:

```powershell
python -m pytest -m unit
```

Run only API tests:

```powershell
python -m pytest -m api
```

Run contract tests against a deployed instance:

```powershell
$env:SERVICE_BASE_URL = "https://your-service-host"
python -m pytest -m contract
```

Run the same command used in CI/CD pipelines:

```powershell
python -m pytest -m "not contract" -q
```

## Shared Setup

Common setup is centralized in:

- `tests/conftest.py` (pytest session setup, auth bypass patching, fixtures, markers)
- `tests/helpers.py` (unittest-compatible `BaseFlaskTest`, `mocked_session`)

This keeps test modules focused on behavior and makes migration to split services simpler.
