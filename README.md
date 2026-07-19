# Library Management Platform

A full-stack library management system for cataloging books, tracking physical copies, managing members, and handling the complete borrowing lifecycle—including due dates, overdue status, returns, fines, and live availability.

The project contains:

- A React and TypeScript web application
- A FastAPI REST service with Swagger/OpenAPI documentation
- A PostgreSQL database accessed through SQLAlchemy
- JWT authentication and role-based authorization
- A gRPC service for internal or service-to-service integrations
- An isolated Behave BDD feature-test suite
- A PDF feature and API presentation deck

## High-level architecture

```mermaid
flowchart LR
    User[Library user or staff] --> UI[React + TypeScript UI]
    UI -->|JWT REST requests| API[FastAPI REST API]
    Client[Internal client] -->|Bearer-token gRPC| GRPC[gRPC service]
    API --> Services[Library service layer]
    GRPC --> Services
    Services --> ORM[SQLAlchemy ORM]
    ORM --> DB[(PostgreSQL)]

    API --> Swagger[Swagger / OpenAPI]
    Tests[Behave feature tests] --> Services
    Tests --> API
    Tests --> TestDB[(Isolated SQLite test DB)]
```

### Application layers

| Layer | Responsibility |
|---|---|
| React UI | Navigation, forms, autocomplete, dashboards, role guards, and user feedback |
| FastAPI | REST contracts, validation, authentication dependencies, and error responses |
| Service layer | Catalog, borrowing, returns, availability, overdue, and fine business rules |
| SQLAlchemy | Models, relationships, queries, and transactions |
| PostgreSQL | Persistent application, authentication, inventory, and circulation data |
| gRPC | Protobuf-based service-to-service operations |
| Behave | Business workflow and HTTP integration verification using an isolated test database |

## Features

### Authentication and authorization

- Email/password login with JWT bearer tokens
- Role-based API and UI access
- Protected routes and user-friendly access-denied states
- Roles: `student`, `librarian`, `admin`, and `visitor`
- Account information and sign-out through the UI profile menu
- Borrow-record ownership checks prevent users from returning another member's loan

### Authors and catalog

- Create and list authors
- Store author biographies
- Create books with ISBN, category, publisher, year, language, and page count
- Search books by partial title
- Filter books by author
- Scrollable author directory with associated book titles
- Click **Books (n)** to open the catalog filtered to an author

### Physical copy inventory

- Register barcode-level physical copies
- Search for the parent book through inline title autocomplete
- Track copy status using an inline status picker
- Supported form statuses: available, checked out, and maintenance
- Show total and currently available copy counts on the same line
- Scrollable availability directory

### Member management

- Create member records
- Store contact, address, joining-date, and status information
- Search by first name, last name, full name, or exact member ID
- Scrollable member table with a sticky header
- Automatically refresh the directory after member creation

### Borrowing

- Search books by title through inline autocomplete
- Display ISBN and live available-copy counts in search results
- Keep zero-availability titles visible but disabled
- Borrow by selected book or a specific copy through the API
- Select the first available physical copy when borrowing by book
- Resolve the member from the authenticated user's email—no client-supplied member ID
- Automatically create a linked member record on first borrow when required
- Validate that the due date is not before the borrow date
- Mark the selected copy as borrowed

### Dashboard, returns, and fines

- Personal loan history for every authenticated borrower role
- Current-loan, overdue-loan, and total-fine summaries
- Book, author, borrow date, due date, status, overdue days, and fine columns
- Loan statuses: `on loan`, `overdue`, and `returned`
- Automatic dashboard refresh every 60 seconds
- Return action records the current date and makes the physical copy available
- Fine calculation at `1.00` per overdue day
- Fine stops accruing when the copy is returned
- Fine-clearance action for returned loans
- Immediate dashboard refresh after return or fine clearance

### APIs and documentation

- FastAPI-generated Swagger UI
- ReDoc reference documentation
- Machine-readable OpenAPI JSON
- Canonical JSON error responses
- Postman collection
- gRPC protobuf contract and server
- Detailed PDF feature/API slide deck with actual UI captures

## Role overview

| Capability | Student | Librarian | Admin | Visitor |
|---|---:|---:|---:|---:|
| Browse catalog | Yes | Yes | Yes | Yes |
| View personal loans | Yes | Yes | Yes | Authenticated view |
| Borrow and return own copies | Yes | Yes | Yes | No |
| Create authors and books | No | Yes | Yes | No |
| Register physical copies | No | Yes | Yes | No |
| Create and search members | No | Yes | Yes | No |

## Repository structure

```text
library/
|-- backend/
|   |-- app/
|   |   |-- api.py              FastAPI routes
|   |   |-- auth.py             JWT authentication and role checks
|   |   |-- services.py         Business logic
|   |   |-- schemas.py          Request and response contracts
|   |   |-- models/             SQLAlchemy models
|   |   |-- db/                 Database setup and seed data
|   |   `-- grpc/               Protobuf contract and gRPC server
|   |-- features/               Behave BDD scenarios and steps
|   |-- postman_collection.json
|   |-- requirements.txt
|   `-- README.md               Backend-specific documentation
|-- frontend/
|   |-- src/
|   |   |-- components/         Pages and shared UI components
|   |   `-- lib/                API and authentication helpers
|   |-- package.json
|   `-- README.md               Frontend-specific documentation
|-- docs/
|   |-- Library-Management-Feature-API-Deck.pdf
|   |-- feature-deck.html
|   `-- ui-screens/
|-- .gitignore
`-- README.md
```

## Prerequisites

Install:

- Python 3.11 or newer
- Node.js 18 or newer with npm
- PostgreSQL
- Git, if cloning from GitHub

## Complete local setup

### 1. Clone the repository

```bash
git clone git@github.com:dhananjaygaikwad1990/library-management-platform.git
cd library-management-platform
```

HTTPS alternative:

```bash
git clone https://github.com/dhananjaygaikwad1990/library-management-platform.git
cd library-management-platform
```

### 2. Create the PostgreSQL database

Create a database named `liberary`, or choose another name and update the backend connection string.

Example using `psql`:

```sql
CREATE DATABASE liberary;
```

### 3. Configure and install the backend

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS or Linux, activate with:

```bash
source .venv/bin/activate
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/liberary
JWT_SECRET_KEY=replace-with-a-secure-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Initialize the schema, roles, and development users:

```bash
python -m app.db.init_db
```

Start the HTTP service:

```bash
python -m app.main
```

The backend runs at `http://localhost:8000`.

### 4. Configure and install the frontend

Open another terminal from the repository root:

```powershell
cd frontend
npm install
```

The default backend URL is already `http://localhost:8000`. To configure another URL, create `frontend/.env`:

```env
VITE_API_BASE=http://localhost:8000
```

Start the UI:

```bash
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## Development accounts

Database initialization creates these development-only users:

| Role | Email | Password |
|---|---|---|
| Librarian | `lib1@example.com` | `LibrarianPass1!` |
| Student | `student1@example.com` | `StudentPass1!` |
| Administrator | `admin1@example.com` | `AdminPass1!` |
| Visitor | `visitor1@example.com` | `VisitorPass1!` |

Replace or remove these credentials before any production deployment.

## API documentation

With the backend running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Health check: `http://localhost:8000/health`

Authenticate through `POST /token`, then use:

```http
Authorization: Bearer <access_token>
```

For the complete endpoint table and request examples, see [backend/README.md](backend/README.md).

## Run the tests

The Behave suite uses `backend/test.db`, an isolated SQLite database. It does not modify the configured PostgreSQL development database.

```powershell
cd backend
behave --no-capture
```

Expected result:

```text
1 feature passed
12 scenarios passed
66 steps passed
```

Verify the frontend production build:

```powershell
cd frontend
npm run build
```

## Start the gRPC server

With the backend virtual environment active:

```powershell
cd backend
python -m app.grpc.server
```

The protobuf contract is located at `backend/app/grpc/library.proto`.

## Key documentation

- [Backend guide](backend/README.md)
- [Frontend guide](frontend/README.md)
- [Feature and Swagger API PDF deck](docs/Library-Management-Feature-API-Deck.pdf)
- [Postman collection](backend/postman_collection.json)
- [BDD feature specification](backend/features/library.feature)

## Production considerations

- Configure a strong `JWT_SECRET_KEY`.
- Restrict CORS to trusted frontend origins.
- Replace/remove development users and API keys.
- Use a managed secret store instead of committed environment values.
- Run PostgreSQL migrations rather than relying only on schema initialization.
- Add a payment/audit ledger if fine clearance represents a real financial transaction.
- Review browser token-storage requirements for the deployment environment.
- Place the API behind TLS and a production process manager or container platform.

## License

No license has been specified. Add a license before distributing or accepting external contributions.
