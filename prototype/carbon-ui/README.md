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

The workbook upload area calls the real FastAPI summary endpoint. Saved project
controls, network-plan save/load, drag-and-drop VM assignment, autosave, and
Terraform ZIP export all use the shared FastAPI/Postgres prototype stack.
The shell includes a workflow progress guide, visible workflow completion
checklists, workflow-header `Step help`, shell-level help, and a separate
user-guide route so evaluators can see what to do next without leaving the
workbench.
Streamlit remains the supported production UI while Carbon is evaluated against
the promotion gates.

## Smoke Test

With Docker Compose running and the Carbon dev server available on
`http://localhost:3000`, run:

```bash
npm run test:e2e
```

The smoke test uploads the bundled small RVTools workbook, saves a Carbon
prototype project, exercises drag-and-drop assignment plus autosave reload,
reloads it from Postgres, and deletes temporary smoke projects.

## Git Hygiene

- Keep Carbon UI work under `prototype/carbon-ui`.
- Keep shared backend work under `prototype/api` until it is promoted.
- Use feature branches and pull requests for Carbon milestones.
- Do not remove or freeze Streamlit while this prototype is being evaluated.
- See `docs/carbon-react-ui-strategy.md` for promotion gates.
- See `docs/carbon-streamlit-parity-roadmap.md` for the next parity work needed
  before Carbon can replace Streamlit.
- See `docs/carbon-promotion-cutover-guide.md` before promoting Carbon as the
  default UI.
