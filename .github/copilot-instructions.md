# Copilot Instructions for Gomoku Repository

## High Level Details

This repository implements a full-stack Gomoku (Five in a Row) game application. The backend provides RESTful APIs and Server-Sent Events (SSE) for real-time game updates, user authentication, and room management. The frontend is a web application for playing the game, joining rooms, and managing user sessions.

The repository is medium-sized with approximately 20-30 files across backend and frontend. It uses a microservices-like architecture with separate backend (Python) and frontend (TypeScript/React) components.

- **Languages**: Python 3.13+ (backend), TypeScript/JavaScript (frontend)
- **Frameworks**: FastAPI (backend), Next.js 16 with React 19 (frontend)
- **Databases**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Other Tools**: Uvicorn for ASGI server, Tailwind CSS for styling, ESLint for linting, Prettier for formatting

## Build Instructions

### Environment Setup

- **Python**: Requires Python 3.13+. Uses `uv` for dependency management. A `.python-version` file indicates pyenv usage.
- **Node.js**: Requires Node.js (version not specified, but Next.js 16 suggests Node 18+). Uses npm for package management.
- **Database**: Requires PostgreSQL. Environment variables in `.env` file for DB connection.

Always set up the database before running the backend. Copy `.env.example` to `.env` and fill in DB credentials.

### Frontend

1. **Bootstrap**: `cd frontend && npm install` - Installs dependencies. Takes ~1-2 minutes.
2. **Lint**: `cd frontend && npm run lint` - Runs ESLint. No errors expected if code follows standards.
3. **Build**: `cd frontend && npm run build` - Builds the Next.js app for production. Takes ~30-60 seconds.
4. **Run Dev**: `cd frontend && npm run dev` - Starts dev server on http://localhost:3000. Auto-reloads on changes.
5. **Run Prod**: `cd frontend && npm run start` - Starts production server after build.

Validated: npm install works, lint passes on clean code, build succeeds, dev server starts successfully.

### Backend

1. **Bootstrap**: `cd backend && uv sync` - Installs Python dependencies. Takes ~1-2 minutes.
2. **Migrations**: `cd backend && uv run alembic upgrade head` - Applies DB migrations. Requires DB connection.
3. **Run Dev**: `cd backend && python scripts/run_dev.py` - Starts dev server with auto-reload on http://0.0.0.0:8000. Checks migrations first.
4. **Run Prod**: `cd backend && python scripts/run_prod.py` - Starts production server without reload.

Validated: uv sync works, migrations apply if DB is set up, dev server starts but requires DB for full functionality. No linting configured for Python.

### Full Stack

- Always run backend first, then frontend.
- Backend needs DB; frontend proxies to backend via axios (configured in lib/axios.ts).
- No tests present; no CI pipelines configured.

Making changes: After code edits, run lint/build for respective parts. For DB schema changes, update models.py, run `uv run alembic revision --autogenerate -m "message"`, then `uv run alembic upgrade head`.

## Project Layout

### Architecture

- **Backend** (`backend/`): FastAPI app in `src/gomoku/`. Main entry: `main.py`. APIs in `api/`, DB models in `sql/models.py`, state management in `state/`.
- **Frontend** (`app/`): Next.js pages in `app/`. Lobby, login, room pages. Hooks in `lib/hooks/`.
- **Config Files**: `backend/pyproject.toml` (deps), `frontend/package.json` (deps/scripts), `alembic.ini` (migrations), `tsconfig.json` (TypeScript).
- **Scripts**: `backend/scripts/run_dev.py` (checks migrations, starts uvicorn), `run_prod.py` (starts uvicorn).

### Validation

- No CI workflows yet. Manual validation: run lint, build, start servers, test game flow.
- Dependencies: PostgreSQL, Node.js, Python 3.13+, uv tool.

### Key Files

- Root: LICENSE, .github/ (for this file), .vscode/ (editor config).
- Backend: pyproject.toml, alembic.ini, src/gomoku/main.py (FastAPI app), sql/models.py (DB models), api/auth.py (JWT auth), api/room.py (room management), sse/game.py (game events).
- Frontend: package.json, app/layout.tsx (root layout), app/page.tsx (home), lobby/page.tsx, room/[id]/page.tsx (game room), lib/axios.ts (API client).

Trust these instructions; they are validated. Only search if issues arise.
