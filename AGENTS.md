# Repository Guidelines

## Project Structure & Module Organization
FastAPI backend lives in `backend/`. `backend/app/core` covers config and auth helpers, `backend/app/services` contains LLM, memory, and session logic, and `backend/app/schemas` stores Pydantic contracts. `backend/main.py` exposes the API. Tests reside in `backend/tests/` split into `unit/`, `integration/`, and `live/`. The React + TypeScript client sits in `frontend/`; UI components live in `frontend/src/components/`, shared state in `frontend/src/contexts/`, helpers in `frontend/src/utils/`, and static assets in `frontend/public/`.

## Build, Test, and Development Commands
Start Ollama with `ollama serve` before launching services. Run `cd backend && pip install -r requirements.txt` once, then `uvicorn main:app --reload --port 8001` (or `python main.py`) for the API. Execute `python -m pytest` for the full backend suite, `-m unit` or `-m integration` to narrow scope, and target LLM flows via `tests/live/test_direct_llm.py`. For the frontend, use `cd frontend && npm install`, then `npm start` for local dev, `npm run build` for production, and `npm test -- --coverage` before release.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, explicit type hints, and FastAPI dependency injection. New service classes belong in `backend/app/services` with descriptive PascalCase names; related schemas live in `backend/app/schemas`. Frontend files use PascalCase components (`GuidedChat.tsx`), camelCase utilities, and colocated styling. Run `npx eslint src --max-warnings=0` to enforce the bundled lint rules.

## Testing Guidelines
Keep fixtures in `backend/tests/conftest.py` synchronized with new data. Use unit tests for isolated services, integration tests for API layers, and reserve live tests for work that hits an active Ollama model. Frontend changes should ship with Jest + React Testing Library specs beside the component under `frontend/src/components/__tests__/`, validating user-facing behavior.

## Commit & Pull Request Guidelines
Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `refactor:`) with imperative summaries under 72 characters. Exclude build artefacts and local databases from commits. Pull requests need a clear summary, affected areas, linked issues, and screenshots or cURL output for visible changes. Call out new environment variables or model downloads for reviewers.

## Security & Configuration Tips
Store secrets in ignored `.env` files; never commit tokens, Ollama configs, or diary exports. Reset or ignore `backend/dear_me.db` before opening a PR. Any change to CORS, authentication, or ports must remain compatible with the React client at `http://localhost:3000` and be documented in `README.md`.
