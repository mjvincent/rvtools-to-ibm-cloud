# Carbon UI Prototype

This is an experimental IBM Carbon Design System shell for the RVTools to IBM
Cloud workbench. Streamlit remains the supported application while this
prototype evaluates whether a Carbon/React experience is worth a later
migration.

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

The workbook upload area calls the real FastAPI summary endpoint. Deeper
planning and export panels are intentionally mocked in this first slice.
