# Library Service Backend

FastAPI and gRPC backend for the library application. It manages authors, books, physical copies, members, borrowing, returns, overdue fines, authentication, and role-based authorization using PostgreSQL and SQLAlchemy.

## Technology

- Python 3.11+
- FastAPI and Uvicorn
- SQLAlchemy 2
- PostgreSQL with `psycopg`
- JWT bearer authentication
- gRPC and Protocol Buffers
- Behave feature tests

## Core behavior

- Authors and catalog books can be created and listed.
- A book can have multiple physical copies identified by unique barcodes.
- Copy statuses include `available`, `checked_out`, and `maintenance`; borrowing changes a selected available copy to `borrowed`, and returning it changes the copy back to `available`.
- Books can be searched by partial title.
- Availability summaries expose total and available copies for every title.
- Members can be created, listed, and searched by name or exact member ID.
- REST borrowing uses the authenticated user's email instead of accepting a member ID from the client.
- If the authenticated account has no member record, its first borrow automatically creates one from the login email and full name.
- Borrow due dates cannot precede borrow dates.
- Active loans become overdue after their due date.
- Fines accrue at `1.00` per overdue day.
- Returning a copy records the current date, finalizes its fine, and makes the copy available.
- A returned loan's outstanding fine can be cleared through the fine-clearance endpoint.
- Users can view and update only their own REST borrow records.

## Project layout

```text
backend/
|-- app/
|   |-- api.py                 FastAPI routes
|   |-- auth.py                JWT and role authorization
|   |-- main.py                Database initialization and HTTP startup
|   |-- schemas.py             Pydantic request/response models
|   |-- services.py            Library business logic
|   |-- db/                    Database engine and initialization
|   |-- grpc/                  Protobuf contract and gRPC server
|   `-- models/                SQLAlchemy models
|-- features/                  Behave feature files and steps
|-- postman_collection.json    Example REST requests
|-- requirements.txt
`-- .env.example
```

## Setup

Run commands from the `backend` directory.

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure PostgreSQL.

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/liberary
JWT_SECRET_KEY=replace-with-a-secure-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

`JWT_SECRET_KEY` and `ACCESS_TOKEN_EXPIRE_MINUTES` are optional in development but should always be explicitly configured outside development.

4. Initialize the schema, roles, and development users.

```bash
python -m app.db.init_db
```

5. Start the HTTP server.

```bash
python -m app.main
```

The server listens on `http://localhost:8000`.

## Development accounts

Database initialization seeds these development-only accounts:

| Role | Email | Password |
|---|---|---|
| Librarian | `lib1@example.com` | `LibrarianPass1!` |
| Student | `student1@example.com` | `StudentPass1!` |
| Administrator | `admin1@example.com` | `AdminPass1!` |
| Visitor | `visitor1@example.com` | `VisitorPass1!` |

The administrator seed also has the student role. Replace or remove these credentials in non-development environments.

## Authentication

Obtain a JWT:

```http
POST /token
Content-Type: application/json

{
  "email": "student1@example.com",
  "password": "StudentPass1!"
}
```

Send the returned token to protected endpoints:

```http
Authorization: Bearer <access_token>
```

Roles are `student`, `librarian`, `admin`, and `visitor`.

## REST API

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/health` | Health check | Public |
| `POST` | `/token` | Authenticate and obtain a JWT | Public |
| `GET` | `/authors` | List authors | Authenticated |
| `POST` | `/authors` | Create an author | Librarian, admin |
| `GET` | `/books` | List/search books | Authenticated |
| `POST` | `/books` | Create a catalog book | Librarian, admin |
| `GET` | `/books/{book_id}` | Get one book | Authenticated |
| `GET` | `/books/availability` | List total/available copy counts | Authenticated |
| `POST` | `/copies` | Register a physical copy | Librarian, admin |
| `GET` | `/members` | List/search members | Librarian, admin |
| `POST` | `/members` | Create a member | Librarian, admin |
| `POST` | `/borrow` | Borrow an available copy for the logged-in user | Student, librarian, admin |
| `GET` | `/me/borrows` | Get the logged-in user's loan history | Student, librarian, admin |
| `POST` | `/me/borrows/{borrow_id}/return` | Return the user's borrowed copy | Student, librarian, admin |
| `POST` | `/me/borrows/{borrow_id}/clear-fine` | Clear a returned loan's fine | Student, librarian, admin |

### Query parameters

- `GET /books?search=<title>` performs a case-insensitive partial-title search.
- `GET /books?author_id=<id>` returns books for one author.
- `GET /books/availability?search=<title>` searches availability by partial title.
- `GET /members?search=<value>` searches first name, last name, full name, or an exact numeric member ID.

List endpoints currently return at most 50 books/availability records and 100 members.

### Borrow request

The client selects a book; the service selects its first available physical copy. `copy_id` may be supplied instead when a specific copy is required.

```json
{
  "book_id": 1,
  "borrow_date": "2026-07-19",
  "due_date": "2026-08-02",
  "remarks": "Optional note"
}
```

`member_id` is intentionally absent. The member is resolved from the bearer token's user email.

## API documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Current AWS EC2 deployment

The deployed FastAPI service runs on an AWS EC2 instance. It is currently exposed to the Vercel frontend through an ngrok HTTPS tunnel:

```text
Vercel UI
  → https://aqua-unable-divinity.ngrok-free.dev
  → ngrok tunnel
  → FastAPI/Uvicorn on AWS EC2
  → PostgreSQL
```

Current public endpoints:

- API base: `https://aqua-unable-divinity.ngrok-free.dev`
- Swagger UI: `https://aqua-unable-divinity.ngrok-free.dev/docs`
- ReDoc: `https://aqua-unable-divinity.ngrok-free.dev/redoc`
- Health check: `https://aqua-unable-divinity.ngrok-free.dev/health`

The frontend is deployed at `https://library-management-platform-2ert-git-main-akgdrive.vercel.app` and uses the ngrok address as `VITE_API_BASE_URL`.

Operational requirements:

- Keep the FastAPI/Uvicorn process running on EC2 using a process manager such as systemd, Supervisor, Docker, or another production runtime.
- Keep the ngrok agent running and forwarding to the correct local FastAPI port, normally `8000`.
- Ensure the EC2 security group exposes only the ports actually required by the deployment.
- Configure backend secrets and `DATABASE_URL` on EC2; do not commit `.env`.
- Update and redeploy the Vercel frontend whenever the ngrok public URL changes.
- Prefer a permanent HTTPS domain or load balancer instead of a temporary ngrok tunnel for stable production use.

## Error responses

Library errors use a consistent structure:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Typical HTTP statuses are `401` for missing/invalid authentication, `403` for insufficient roles, `404` for missing records, `409` for database conflicts, and `422` for library validation errors.

## gRPC

The contract is located at `app/grpc/library.proto`. Start the server with:

```bash
python -m app.grpc.server
```

gRPC requests require bearer-token metadata. The gRPC contract retains explicit member/copy identifiers for service-to-service and internal callers; the email-derived member behavior applies to the REST self-service borrow flow.

## Verification and tests

Compile/import verification:

```bash
python -m py_compile app/services.py app/schemas.py app/api.py
python -c "from app.main import app; print('Backend import successful')"
```

Run Behave scenarios:

```bash
behave
```

The Behave suite uses an isolated SQLite database and covers catalog search/filtering, authors, copy inventory and availability, member search, automatic member linking, borrowing validation, unavailable copies, overdue fines, returns, fine clearance, ownership protection, authentication, role authorization, HTTP borrow/return flows, conflicts, and missing records. Scenario cleanup does not modify the configured development database.

Generate an HTML Behave report:

```bash
behave --format html --outfile reports/behave-report.html
```

## Operational notes

- Fine clearance currently represents marking a fine as cleared; it is not connected to a payment processor or payment audit ledger.
- Copy availability is calculated from current copy statuses.
- CORS currently allows all origins, methods, and headers. Restrict this for production.
- The fallback JWT secret is development-only. Always configure a strong secret in production.
