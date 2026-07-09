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

## Current State

- Application CI/CD testing is currently not working
- Need better abstraction hidding data/information
- Shorter cleaner code
- Speed up processing allow for concurrent processing
- Changing password break the salt and secrets of new password

## Security Notes

Because this is a password storage application, make sure secrets, database credentials, and any encryption keys are never committed to the repository.
