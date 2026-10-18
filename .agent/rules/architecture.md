# Architecture Rules

Before adding a new module or abstraction, inspect the existing architecture.

Prefer extending existing patterns rather than introducing parallel frameworks.

Keep clear separation between:

- HTTP/API layer (`backend/app/routers/`, `backend/app/schemas/`)
- business logic & scheduling (`backend/app/services/`)
- persistence/data-access layer (`backend/app/database/` — SQLAlchemy async ORM & CRUD)
- external service integrations (`backend/app/services/tencent_api.py`)
- frontend UI (`frontend/src/components/`), state/polling hooks (`frontend/src/hooks/`), and API client (`frontend/src/services/api.ts`)

Do not place substantial business logic directly inside FastAPI route handlers or React UI components.

Keep synchronous blocking I/O (such as `urllib.request` market data fetches) off the async event loop using `run_in_executor`.

Avoid circular dependencies.

When a requested change has significant architectural implications, explain the proposed design before implementing it.

