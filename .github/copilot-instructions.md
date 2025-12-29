# Copilot Instructions for Gomoku Repository

## Repository Summary

This repository implements a Gomoku (五子棋) game application with a backend API and a frontend web interface. The backend provides user authentication and management services, while the frontend is a Next.js application for the game interface. Currently, the backend is fully implemented with user CRUD operations, JWT authentication, and database migrations, but the frontend is still in its initial Next.js template state.

## High-Level Repository Information

- **Size**: Small repository with ~200 lines of backend code and minimal frontend code.
- **Type**: Full-stack web application.
- **Languages**: Python 3.13+ (backend), TypeScript/JavaScript (frontend).
- **Frameworks/Runtimes**:
  - Backend: FastAPI with SQLAlchemy Core (async), Alembic for migrations, PostgreSQL database, JWT for authentication.
  - Frontend: Next.js 16 with React 19, TypeScript, Tailwind CSS.
  - Package Management: uv (backend), npm (frontend).
- **Target Runtime**: Backend runs on Python 3.13+, frontend on Node.js.

## Build Instructions

### Backend Setup and Build

1. **Environment Setup**: Copy `backend/.env.example` to `backend/.env` and fill in the database credentials. The application uses PostgreSQL.
2. **Install Dependencies**: Run `cd backend && uv sync` to install Python dependencies using uv.
3. **Database Migration**: Run `cd backend && uv run alembic upgrade head` to apply database migrations.
4. **Run Server**: Execute `cd backend && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000` to start the FastAPI server.
   - The server will be available at http://localhost:8000
   - API documentation at http://localhost:8000/docs
5. **Validation**: The server should start without errors if database connection is successful. Test with `curl http://localhost:8000/` which should return a welcome message.

**Notes**:

- Always run `uv sync` after modifying `pyproject.toml`.
- Database must be accessible; if connection fails, check `.env` values.
- No tests are currently implemented in the backend.
- Build time: < 1 minute for dependencies, < 10 seconds for server start.

### Frontend Setup and Build

1. **Install Dependencies**: Run `cd frontend && npm install` to install Node.js dependencies.
2. **Run Development Server**: Execute `cd frontend && npm run dev` to start the Next.js development server.
   - The app will be available at http://localhost:3000
3. **Build for Production**: Run `cd frontend && npm run build` to create a production build.
4. **Start Production Server**: After building, run `cd frontend && npm run start` to start the production server.
5. **Lint**: Run `cd frontend && npm run lint` to check code style with ESLint.

**Notes**:

- Always run `npm install` after modifying `package.json`.
- Development server supports hot reloading.
- Build time: < 1 minute for dependencies, < 30 seconds for build.
- No tests are currently implemented in the frontend.

### Testing

- No automated tests are currently implemented in either backend or frontend.
- Manual testing: Use the API endpoints via Swagger UI at `/docs` or curl commands.

### Validation Steps

- Backend: Check that `uv run uvicorn src.main:app` starts without import errors.
- Frontend: Verify that `npm run dev` starts the server and the page loads at localhost:3000.
- Database: Ensure PostgreSQL is running and credentials in `.env` are correct.
- Always verify database connectivity before running the backend.

## Project Layout and Architecture

### Major Architectural Elements

- **Backend (`backend/`)**: FastAPI application with SQLAlchemy Core for database operations.
  - `src/main.py`: Main FastAPI app with user CRUD endpoints.
  - `src/models.py`: SQLAlchemy table definitions.
  - `src/database.py`: Database connection and lifecycle management.
  - `src/jwt.py`: JWT token creation and validation.
  - `src/schemas.py`: Pydantic models for API requests/responses.
  - `alembic/`: Database migration scripts.
- **Frontend (`frontend/`)**: Next.js application (currently default template).
  - `app/page.tsx`: Main page component.
  - `lib/axios.ts`: Axios configuration for API calls.
- **Configuration Files**:
  - Backend: `pyproject.toml` (dependencies), `alembic.ini` (migration config), `.env` (environment variables).
  - Frontend: `package.json` (dependencies), `next.config.ts`, `tsconfig.json`, `eslint.config.mjs`.

### Checks and Validation Pipelines

- No GitHub Actions or CI pipelines are currently configured.
- Pre-commit checks: ESLint for frontend code style.
- Manual validation: Test API endpoints and frontend functionality.

### Dependencies

- Backend requires PostgreSQL database (remote or local).
- Environment variables must be set in `.env` for database connection and JWT secret.
- Python 3.13+ required (specified in `pyproject.toml`).

### Repository Structure Details

**Root Directory Files**:

- `LICENSE`: MIT license file.
- `.git/`: Git repository.
- `.vscode/`: VS Code workspace settings.
- `backend/`: Backend Python application.
- `frontend/`: Frontend Next.js application.

**Backend Key Files**:

- `pyproject.toml`: Project metadata and dependencies (FastAPI, SQLAlchemy, etc.).
- `.env.example`: Template for environment variables.
- `src/main.py` (excerpt):

  ```python
  from fastapi import FastAPI
  from database import init_db, shutdown_db
  from models import metadata

  app = FastAPI(title="FastAPI SQLAlchemy Core Async Demo")

  @app.on_event("startup")
  async def startup_event():
      await init_db(metadata)

  @app.on_event("shutdown")
  async def shutdown_event():
      await shutdown_db()
  ```

**Frontend Key Files**:

- `package.json`: Dependencies (Next.js, React, Tailwind, etc.).
- `app/page.tsx`: Default Next.js home page.

Trust these instructions and only search for additional information if something is incomplete or incorrect. This will help you work efficiently on this repository.
