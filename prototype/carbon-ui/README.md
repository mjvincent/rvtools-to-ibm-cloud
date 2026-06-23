# Carbon UI Prototype

This is an experimental IBM Carbon Design System shell for the RVTools to IBM
Cloud workbench. Streamlit remains the supported production application while
this prototype evaluates whether a Carbon/React experience is worth a later
migration.

This is not a fork of the Streamlit app. It is a parallel prototype that calls
the shared FastAPI layer under `prototype/api`.

## Run Locally

Start the prototype API from the repository root:

```bash
uvicorn prototype.api.app:app --reload --port 8000
```

Then start the frontend:

```bash
cd prototype/carbon-ui
npm install
npm run dev
```

Open `http://localhost:3000`.

The workbook upload area calls the real FastAPI summary endpoint. The saved
project controls call the real FastAPI/Postgres project endpoints. Deeper
planning and export panels are intentionally mocked in this first slice.

## Smoke Test

With Docker Compose running and the Carbon dev server available on
`http://localhost:3000`, run:

```bash
npm run test:e2e
```

The smoke test uploads the bundled small RVTools workbook, saves a Carbon
prototype project, reloads it from Postgres, and deletes the temporary project.

## Git Hygiene

- Keep Carbon UI work under `prototype/carbon-ui`.
- Keep shared backend work under `prototype/api` until it is promoted.
- Use feature branches and pull requests for Carbon milestones.
- Do not remove or freeze Streamlit while this prototype is being evaluated.
- See `docs/carbon-react-ui-strategy.md` for promotion gates.
