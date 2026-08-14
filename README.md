# Password Keeper

**Author:** Daniel Durant

## About

Password Keeper is a Flask-based password management API for storing and retrieving passwords securely. It also includes features for generating new passwords and tracking password history.

## Features

- User management
- Role-based access support
- Password storage and retrieval
- Password history tracking
- Folder organization
- Security questions
- Audit logging
- Swagger UI documentation
- Rate limiting
- Caching
- CORS support

## Requirements

- Python 3.11+ recommended
- MySQL database for development
- A `.env` file with a `PASSWORD` value for your database password

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root and add your database password:

   ```env
   PASSWORD=your_mysql_password
   ```
5. Make sure a MySQL database named `PasswordKeeper` exists locally.

## Virtual Environment (Recommended)

On Windows, virtual environment launchers store absolute paths. If the project folder moves (or differs across machines), `pip.exe` can fail with a launcher error.

Use this workflow on each machine instead of copying `myenv`:

1. Create a fresh virtual environment in the project root:

   ```powershell
   py -3.13 -m venv myenv
   ```
2. Activate it:

   ```powershell
   .\myenv\Scripts\Activate.ps1
   ```
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

If you ever see a launcher/path error for `pip`, recreate `myenv` with the same steps above.

## Running the Application

Start the app with:

```bash
python app.py
```

By default, the app runs in development mode and creates the database tables on startup.

## API Documentation

Swagger UI is available at:

```text
/password-keeper-api/docs/
```

The OpenAPI definition is loaded from:

```text
/static/swagger.yaml
```

## Testing

A testing configuration is available in `config.py` using an in-memory SQLite database. If you add or run tests, use `TestingConfig` for isolated test execution.

## Error Response Contract

The API uses a consistent error payload for failed requests so both humans and clients can understand what went wrong.

### Standard response shape

```json
{
  "status": "error",
  "message": "Human-readable explanation",
  "error_code": "stable_machine_readable_code",
  "details": {
    "code": "stable_machine_readable_code",
    "domain": "user|role|folder|password|security_question|resource",
    "operation": "create|lookup|delete|update",
    "message": "More context about the failure"
  }
}
```

### Notes

- `message` is intended for human readers.
- `error_code` is stable for client-side handling.
- `details` provides domain-specific context such as the affected resource type and operation.

### Common error examples

- `user_already_exists`
- `invalid_password`
- `role_not_found`
- `user_not_found`
- `folder_not_found`
- `password_not_found`
- `question_not_found`
- `delete_forbidden`

## CI/CD Workflows

This repo now includes two GitHub Actions workflows:

- `.github/workflows/main.yaml`
  - Runs tests on `pull_request` and `push` for `main`, `master`, and `develop`.
  - Uses `pytest -m "not contract" -q` for fast CI checks.
- `.github/workflows/deploy.yaml`
  - Runs tests before deployment.
  - Manual-only (`workflow_dispatch`) while deployment is not enabled.
  - Supports `staging` and `production` targets when secrets are configured.

### Pre-Main Version Flow

Use `develop` as your "next version" branch:

1. Create feature branches from `develop`.
2. Open PRs into `develop` and let CI validate changes.
3. Deploy `develop` to staging for QA.
4. Merge `develop` into `main` when ready for production.

If you are not deploying yet, you can ignore `.github/workflows/deploy.yaml`. Your CI checks in `.github/workflows/main.yaml` still run on push/PR and validate tests.

### Deployment Secrets

Configure these repository/environment secrets for SSH deploys:

- Staging:
  - `STAGING_SSH_HOST`
  - `STAGING_SSH_USER`
  - `STAGING_SSH_KEY`
  - `STAGING_DEPLOY_PATH`
- Production:
  - `PRODUCTION_SSH_USER`
  - `PRODUCTION_SSH_KEY`
  - `PRODUCTION_DEPLOY_PATH`
  - `PRODUCTION_SSH_HOST`

### Recommended GitHub Branch Protection

In GitHub settings, protect `main` and require the CI check from `.github/workflows/main.yaml` before merge. This enforces testing before code lands in production.

## Current State

- CI/CD Pipeline [X]
- Unit Testing [X]
- Better abstraction (in progress) [1/2]
- Make the system as loosely coupled as possible (in progress) []
- Speed up processing allow for concurrent processing [X]

## Security Notes

Because this is a password storage application, make sure secrets, database credentials, and any encryption keys are never committed to the repository.
