# Carbon Operations Runbook

This runbook covers the local/team Docker Compose deployment that runs
Streamlit, Carbon, FastAPI, Postgres, and the shared artifact volume.

Streamlit remains the supported production UI until Carbon passes the promotion
gates. These procedures make the Carbon path operable during shadow, pilot, and
promotion testing without splitting the repository or weakening the Streamlit
fallback.

## Runtime Components

The Compose stack uses these service and volume names:

| Component | Compose name | Purpose |
| --- | --- | --- |
| Carbon UI | `carbon-ui` | Next.js Carbon workbench on `http://localhost:3000`. |
| Streamlit | `app` | Supported production workbench on `http://localhost:8501`. |
| FastAPI | `api` | Upload, project persistence, network plan, preflight, and ZIP APIs on `http://localhost:8000`. |
| Postgres | `postgres` | Project metadata and saved planning-state JSON. |
| Database volume | `postgres-data` | Persistent Postgres data directory. |
| Artifact volume | `rvtools-artifacts` | Uploaded RVTools workbooks and generated artifacts. |

Health endpoints:

| Component | Health check |
| --- | --- |
| Carbon UI | `http://localhost:3000` |
| Streamlit | `http://localhost:8501/_stcore/health` |
| FastAPI | `http://localhost:8000/health` |
| Postgres | `pg_isready -U rvtools -d rvtools` inside the `postgres` container |

## Start, Stop, and Inspect

Start the persistent stack:

```bash
make run
```

Or start directly with Docker Compose:

```bash
docker compose up --build --detach
```

Stop without deleting saved projects or artifacts:

```bash
docker compose down
```

Inspect current service state:

```bash
docker compose ps
```

Inspect recent logs:

```bash
docker compose logs --tail=100 api
docker compose logs --tail=100 carbon-ui
docker compose logs --tail=100 app
docker compose logs --tail=100 postgres
```

Follow logs during a workflow test:

```bash
docker compose logs --follow api carbon-ui app postgres
```

## Backup Procedure

Back up both persistent stores before a Carbon pilot, release-candidate test, or
data migration:

1. Export project metadata and saved planning-state JSON from Postgres.
2. Archive uploaded workbooks and generated artifacts from `rvtools-artifacts`.
3. Keep source RVTools workbooks, exported `planning-state.json` files, and
   downloaded Terraform ZIPs outside the container volumes.

Create a local backup directory:

```bash
mkdir -p backups
```

Back up Postgres:

```bash
docker compose exec -T postgres pg_dump -U rvtools -d rvtools > backups/rvtools-postgres.sql
```

Back up the artifact volume:

```bash
docker run --rm \
  -v rvtools-to-ibm-cloud_rvtools-artifacts:/data:ro \
  -v "$PWD/backups":/backup \
  alpine tar czf /backup/rvtools-artifacts.tgz -C /data .
```

If the Compose project name is different, find the exact volume name first:

```bash
docker volume ls | grep rvtools-artifacts
```

For platform-managed deployments, use the platform's native database snapshot
and persistent-volume backup mechanism instead of host-local Docker commands.

## Restore Procedure

Use restore for a test drill before production promotion and after any
data-loss incident. Restore into a clean database volume or a deliberately
replaced environment. If existing data might still be needed, preserve a copy of
the current volumes before applying a backup.

Stop the stack:

```bash
docker compose down
```

Start Postgres so the database is available:

```bash
docker compose up --detach postgres
```

Restore Postgres:

```bash
docker compose exec -T postgres psql -U rvtools -d rvtools < backups/rvtools-postgres.sql
```

Restore artifacts into a clean or deliberately replaced artifact volume:

```bash
docker run --rm \
  -v rvtools-to-ibm-cloud_rvtools-artifacts:/data \
  -v "$PWD/backups":/backup \
  alpine sh -c "cd /data && tar xzf /backup/rvtools-artifacts.tgz"
```

Start the full stack:

```bash
docker compose up --build --detach
```

Verify recovery:

1. Confirm `docker compose ps` reports healthy services.
2. Open Streamlit and confirm saved projects are listed.
3. Open Carbon and confirm saved projects are listed.
4. Load a restored project in Carbon.
5. Re-upload the source RVTools workbook if the workflow needs workbook-derived
   dataframe context.
6. Generate a Terraform ZIP and compare expected handoff files.
7. Export `planning-state.json` from Carbon or Streamlit as a project-level
   recovery copy.

## Monitoring Signals

During Carbon shadow and pilot use, track these signals:

| Area | Signal | First check |
| --- | --- | --- |
| Upload | Workbook summary failures, parse errors, unexpected blocker counts | `docker compose logs api` |
| Persistence | Save, load, delete, autosave, or 503 persistence banner events | `docker compose logs api postgres` |
| Carbon UI | Browser workflow failures, failed API calls, package preview issues | `docker compose logs carbon-ui api` |
| Export | Terraform ZIP failures, preflight blocker spikes, missing handoff files | `docker compose logs api` |
| Data growth | Postgres and artifact volume growth | `docker system df`, `docker volume inspect` |
| Fallback readiness | Streamlit health and package generation from the same workbook | `docker compose logs app` |

Minimum promotion expectation:

- health checks are visible for all four services
- API and UI logs are accessible to the support owner
- Postgres and artifact backups are scheduled or documented for the platform
- restore has been tested at least once in a non-production environment
- Streamlit rollback remains available during the stabilization window

## Incident Response

If Carbon is unavailable:

1. Keep Streamlit available as the active production path.
2. Check `carbon-ui` health and logs.
3. Check `api` health because Carbon depends on FastAPI.
4. Preserve the failing project ID, workbook name, browser console error, and
   relevant service logs.

If persistence is unavailable:

1. Confirm Postgres health.
2. Check `api` logs for `DATABASE_URL` or connection failures.
3. Use planning-state JSON export/import for project-level continuity.
4. Do not delete volumes while investigating.

If package generation regresses:

1. Generate the same package in Streamlit when possible.
2. Save the Carbon project state and generated ZIP.
3. Compare handoff inventory and `migration-manifest.json`.
4. Open a regression issue with commit, project ID, workbook, expected output,
   and observed output.

If the database or artifact volume is corrupt:

1. Stop the stack.
2. Preserve a copy of the current volumes before attempting recovery.
3. Restore from the most recent verified backup.
4. Re-run the restore verification checklist.

## Data Handling

RVTools workbooks, saved project state, generated Terraform, handoff CSVs, and
logs can contain sensitive infrastructure data.

Operational requirements before shared Carbon use:

- use authenticated access and HTTPS
- restrict access to approved migration users
- define retention for uploaded workbooks, generated artifacts, backups, logs,
  and browser downloads
- keep IBM Cloud API keys in approved secret mechanisms only
- keep Terraform state files out of the repository
- store backups in an approved encrypted location
- document the support owner, incident contact, and rollback decision maker

## Promotion Evidence Checklist

For Gate 6, record evidence that:

- Docker Compose starts `app`, `api`, `carbon-ui`, and `postgres`
- all configured health checks pass
- a Postgres backup is created and restorable
- the artifact volume backup is created and restorable
- logs can be collected for upload, save/load, autosave, and ZIP export failures
- support ownership and rollback authority are assigned
- Streamlit remains available until the Carbon go/no-go review is approved
