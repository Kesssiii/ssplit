# Split Bills Backend

A small Flask API for tracking shared household bills.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app main run --debug
```

The API runs at `http://127.0.0.1:5000`.

## Backend areas

- `GET /api/health` checks that the backend is running.
- `POST /api/auth/register` creates an account.
- `POST /api/auth/login` verifies credentials and returns a bearer token.
- `GET /api/auth/me` returns the logged-in user.
- `POST /api/auth/logout` invalidates the current bearer token.
- `GET /api/scheduled-bills` lists recurring bills.
- `POST /api/scheduled-bills` creates a recurring bill.
- `GET /api/bills` lists bills.
- `POST /api/bills` creates a bill.
- `GET /api/shared-bills` lists bills shared by the roommates.
- `POST /api/shared-bills` creates a shared bill.
- `GET /api/expenses/overview` returns totals and balances.

## Authentication example

Register:

```json
{
  "email": "noah@example.com",
  "password": "a-password-with-8-characters"
}
```

Use the returned token on protected requests:

```text
Authorization: Bearer <token>
```

Passwords are stored as salted scrypt hashes. Session tokens are only stored as SHA-256 hashes and expire after seven days. The SQLite database is created at `instance/ssplit.sqlite3`.

The authentication routes are implemented. The scheduled-bill, bill, shared-bill, and expense-overview data operations remain intentional `501 Not Implemented` stubs in `app/data.py`.

## Database migrations

Migration files live in `migrations/` and use a numeric prefix for their order, for example `002_add_households.sql`. Migrations run automatically when the Flask app starts. Applied versions are recorded in the `schema_migrations` table and are not run again.
