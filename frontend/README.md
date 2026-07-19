# Library UI

React and TypeScript frontend for the library service. The UI provides authenticated, role-aware catalog, inventory, member, borrowing, return, overdue-fine, and availability workflows.

## Technology

- React 18
- TypeScript
- React Router
- Vite
- Native Fetch API

## Setup

Run commands from the `frontend` directory.

1. Install dependencies.

```bash
npm install
```

2. Configure the backend URL when it differs from the default.

Create a `.env` file:

```env
VITE_API_BASE=http://localhost:8000
```

If unset, the UI uses `http://localhost:8000`.

3. Start the development server.

```bash
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

The backend must be running separately. See `../backend/README.md` for its setup.

## Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Start the Vite development server |
| `npm run build` | Type-check and create a production bundle in `dist/` |
| `npm run preview` | Preview the production bundle locally |

## Authentication and session behavior

- The login screen sends credentials to `POST /token`.
- The JWT, email, and roles are stored in browser `localStorage` under `library_session`.
- API requests automatically include `Authorization: Bearer <token>`.
- Protected routes redirect unauthenticated users to login.
- Page-level role guards show an access-denied message when a role is insufficient.
- Account email, roles, and sign-out are available from the top-right profile menu.

## Roles and pages

| Page | Route | Purpose | UI access |
|---|---|---|---|
| Login | `/login` | Authenticate | Public |
| Dashboard | `/dashboard` | Personal loans, due dates, returns, and fines | Authenticated |
| Authors | `/authors` | Create authors and browse authors/books | Librarian, admin |
| Books | `/books` | Browse the catalog and filtered author titles | Authenticated |
| Book Copies | `/copies` | Register copies and review availability | Librarian, admin |
| Members | `/members` | Create and search members | Librarian, admin |
| Borrow | `/borrow` | Search and borrow an available book | Student, librarian, admin |

## UI workflows

### Dashboard and personal loans

The dashboard loads the authenticated user's loan history immediately and refreshes it every 60 seconds. It displays:

- Current-loan count
- Overdue-loan count
- Total outstanding fines
- Book title and author
- Borrow and due dates
- Loan status: `on loan`, `overdue`, or `returned`
- Overdue days
- Fine amount
- Loan actions

Available actions:

- **Return copy** records the return, finalizes any overdue fine, and makes the physical copy available.
- **Clear fine** appears after an overdue copy is returned and marks the outstanding fine as cleared.

The UI refreshes the loan table immediately after either action.

### Authors

- Librarians and administrators can create authors.
- A scrollable directory lists every author, biography, and associated titles.
- The **Books (n)** link opens `/books?author_id=<id>` and displays only that author's books.
- The Books page provides **View all books** to clear this filter.

### Books

- The catalog lists ID, title, ISBN, category, publisher, and publication year.
- Author links can open the catalog with an `author_id` filter.
- Empty filtered results show a clear message.

### Book copies and availability

- The copy-creation form searches books by title instead of asking for a raw book ID.
- Search begins after two characters and is debounced by 300 milliseconds.
- Results appear in an inline autocomplete and show title and ISBN.
- The selected book ID is submitted internally.
- Copy statuses are selected with an inline, color-coded picker: **Available**, **Checked out**, or **Maintenance**.
- A scrollable availability list displays each title with both counts on the same line:

```text
Book title  Total: 5  Available: 3
```

- Availability refreshes after a copy is created.

### Members

- Librarians and administrators can create member records.
- The directory can search by partial first name, last name, full name, or exact member ID.
- Search requests are debounced by 300 milliseconds.
- Results appear in a scrollable table with a sticky header.
- The list displays member ID, name, email, phone, joining date, and status.
- The directory refreshes after a member is created.

### Borrowing

- The form searches books by title using an inline autocomplete.
- Each result displays title, ISBN, and live available-copy count.
- Titles with zero available copies remain visible but cannot be selected.
- The UI submits the selected book ID, borrow date, due date, and optional remarks.
- Member ID is not requested. The backend links the borrow to the authenticated user's email and automatically creates the member record on first borrow when necessary.
- The backend selects an available physical copy and rejects invalid dates or unavailable titles.

## API integration

The API helper is in `src/lib/api.ts`. It:

- Reads `VITE_API_BASE`.
- Adds JSON content headers.
- Adds the stored bearer token.
- Converts unsuccessful API responses into user-facing errors.

Important UI requests include:

| Request | UI use |
|---|---|
| `POST /token` | Login |
| `GET /authors` | Author directory |
| `POST /authors` | Create author |
| `GET /books` | Catalog, autocomplete, and author filtering |
| `GET /books/availability` | Availability list and borrow autocomplete |
| `POST /copies` | Register a physical copy |
| `GET /members` | Searchable member directory |
| `POST /members` | Create member |
| `POST /borrow` | Borrow a selected title |
| `GET /me/borrows` | Dashboard loan history |
| `POST /me/borrows/{id}/return` | Return a copy |
| `POST /me/borrows/{id}/clear-fine` | Clear a returned loan's fine |

## Production build

Create the optimized bundle:

```bash
npm run build
```

Preview it locally:

```bash
npm run preview
```

The production output is written to `dist/`.

## Troubleshooting

- If new controls are not visible, restart the Vite server and hard-refresh the browser to clear the previous bundle.
- If requests fail, verify that the backend is running and `VITE_API_BASE` points to it.
- If a page shows **Access denied**, check the roles returned at login.
- If a borrow search result shows `0 available`, add or return an available physical copy before borrowing.
- If a token expires, sign out and log in again.

## Current limitations

- Fine clearance is a simulated “mark as cleared” operation; there is no payment gateway or payment-history screen.
- Sessions are stored in `localStorage`; production deployments should review storage and token-lifetime requirements.
- The navigation is shared, while individual management pages enforce their own role guards.
