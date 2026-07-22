# Carbon Hosted Operations Readiness Checklist

**Created**: 2026-07-22
**Purpose**: Define the hosted or pilot-runtime evidence required before
Carbon can move beyond local prototype evaluation.

Streamlit remains the supported production UI and rollback path until this
checklist is complete, reviewed, and accepted in the Carbon promotion gate
review.

## Hosted Runtime Decision Record

| Field | Value |
| --- | --- |
| Target platform |  |
| Carbon route |  |
| FastAPI route |  |
| Streamlit fallback route |  |
| Postgres service |  |
| Artifact storage location |  |
| Authentication and access model |  |
| HTTPS/TLS termination |  |
| Support owner |  |
| Operations owner |  |
| Security/data owner |  |
| Rollback decision maker |  |
| Pilot start/end window |  |

## Required Hosted Evidence

| Gate | Required evidence | Status |
| --- | --- | --- |
| Health checks | Carbon UI, FastAPI `/health`, Streamlit `/_stcore/health`, and Postgres health are visible in the hosted platform. | Not started |
| Alerting | Alerts exist for failed health checks, API 5xx spikes, persistence failures, Terraform ZIP generation failures, and storage threshold breaches. | Not started |
| Logs | Carbon UI, FastAPI, Streamlit, and Postgres logs are centralized, searchable by service, retained for the approved period, and accessible to the support owner. | Not started |
| Retention | Runtime logs, access logs, Postgres backups, artifact backups, generated ZIPs, uploaded workbooks, and incident bundles have approved retention periods. | Not started |
| Backup | Postgres and artifact storage backups are scheduled or platform-managed, encrypted, access-controlled, and tested outside local Docker. | Not started |
| Restore | A non-production hosted restore drill proves saved projects, planning-state JSON, and artifact records can be recovered. | Not started |
| Artifact handling | Uploaded RVTools workbooks, generated Terraform ZIPs, readiness reports, and screenshots are treated as sensitive infrastructure data. | Not started |
| Access control | The hosted route requires authenticated access for approved migration users and uses HTTPS. | Not started |
| Support ownership | Product, technical, operations, security/data, primary support, secondary support, and rollback roles have named owners. | Not started |
| Rollback | Streamlit fallback is reachable, rollback authority is named, and rollback criteria are documented for blocked users, data uncertainty, or package regressions. | Not started |

## Minimum Alert Set

- Carbon UI route unavailable.
- FastAPI `/health` unavailable.
- Streamlit fallback `/_stcore/health` unavailable.
- Postgres health, storage, or connection pressure crosses threshold.
- API 5xx rate or persistence failures increase.
- Terraform ZIP generation fails.
- Artifact storage crosses the agreed usage threshold.
- Backup or restore job fails.

## Minimum Retention Decisions

| Data | Decision required |
| --- | --- |
| Runtime service logs | Retention period, log sink, access group, and masking expectations. |
| Security/access logs | Retention period aligned to enterprise policy. |
| Uploaded RVTools workbooks | Whether hosted persistence is allowed and when files are deleted. |
| Generated Terraform ZIPs | Whether generated packages persist, where they are stored, and who can access them. |
| Postgres backups | Schedule, encryption, restore target, and retention window. |
| Artifact backups | Schedule, encryption, restore target, and retention window. |
| Incident bundles | Approved private tracker, redaction rules, and closure criteria. |

## Restore Drill Acceptance Criteria

1. Restore Postgres into a non-production hosted environment.
2. Restore artifact storage into the same environment.
3. Confirm Carbon, FastAPI, Streamlit fallback, and Postgres health checks pass.
4. Load a restored Carbon project.
5. Re-upload the matching RVTools workbook when workbook-derived context is
   needed.
6. Generate a Carbon Terraform ZIP and confirm expected handoff inventory.
7. Confirm Streamlit fallback remains available for the same workbook.
8. Record restore duration, operator, source backup label, target environment,
   and any data gaps.

## Go / No-Go Rule

Carbon hosted pilot should remain `No-go` until every required hosted evidence
gate is `Pass` or explicitly accepted by the product owner, operations owner,
security/data owner, and rollback decision maker.
