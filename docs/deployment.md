# Deployment Guide

This app is a Streamlit/Python application. Users can access it through a web browser, but the app is not a static HTML site because RVTools workbook parsing, readiness logic, pricing logic, session state, Terraform rendering, and ZIP generation run in Python.

## Deployment Options
The current application is already a browser-based experience when Streamlit is running. It is not a pure static HTML application.

Use one of these patterns:

| Pattern | Best for | Notes |
| --- | --- | --- |
| Local Streamlit | Individual assessments and sensitive customer data that should stay on one workstation. | Run `streamlit run app.py` and use the local browser URL. |
| Local container | Validating deployment behavior before sharing the app. | Builds and runs the same container used by hosted platforms. |
| Hosted private Streamlit container | Migration teams that need shared browser access. | Recommended for team use; require authentication and HTTPS. |
| Static HTML landing page | Intranet navigation or documentation only. | Can link to the Streamlit app, but cannot replace the Python backend. |
| Full web app rewrite | Multi-user saved projects, database-backed workflows, audit trails, or enterprise productization. | Larger architecture change; not required for the current migration workbench. |

## Recommended Deployment Model
For migration team use, deploy the app as a private containerized Streamlit service rather than exposing a public unauthenticated app.

Recommended order:
1. Run locally for individual assessment work.
2. Run the included container image for team validation.
3. Deploy the container to IBM Cloud Code Engine or an internal container platform.

IBM Cloud Code Engine is a good first hosted target because it can run containerized web apps and supports Dockerfile-based source builds. IBM documents that Code Engine apps default to port `8080` unless the app is created with another port, and that private visibility can keep an app off the public internet.

Official references:
- https://cloud.ibm.com/docs/codeengine?topic=codeengine-getting-started
- https://cloud.ibm.com/docs/codeengine?topic=codeengine-application-workloads
- https://cloud.ibm.com/docs/codeengine?topic=codeengine-cli

Streamlit's Docker deployment guidance is also useful for local and container-platform validation:
- https://docs.streamlit.io/deploy/tutorials/docker
- https://docs.streamlit.io/deploy/concepts

## Local Container Run
Build the image from the repository root:

```bash
docker build -t rvtools-to-ibm-cloud .
```

Run the app locally:

```bash
docker run --rm -p 8501:8501 rvtools-to-ibm-cloud
```

Open:

```text
http://localhost:8501
```

The container health check uses Streamlit's health endpoint at `/_stcore/health`.

## IBM Cloud Code Engine
The container command honors Code Engine's `PORT` environment variable. If no `PORT` is provided, it defaults to `8501` for local use. When creating a Code Engine app for this container, set `--port 8501` so Code Engine routes traffic to the Streamlit listener instead of assuming the default app port.

One common private Code Engine flow is:

```bash
ibmcloud login
ibmcloud plugin install code-engine
ibmcloud ce project select --name <project-name>
ibmcloud ce application create \
  --name rvtools-to-ibm-cloud \
  --build-source . \
  --port 8501 \
  --visibility=private
```

Use the generated application URL to access the Streamlit workbench. If the deployment should be intentionally public, omit `--visibility=private` only after confirming the access-control model.

For production or shared-team use, configure access control through the hosting environment, ingress, reverse proxy, or enterprise SSO pattern approved for the deployment. A private Code Engine endpoint limits network exposure, but it is not the same thing as user authentication.

Operational notes:
- Use an IBM Cloud project, resource group, and region approved for the migration data.
- Use an IBM Cloud Container Registry namespace or Code Engine source build process approved by the account team.
- Keep `--port 8501` aligned with the Streamlit container listener.
- Use private visibility when the app should not be reachable from the public internet.
- Document who can access uploaded RVTools workbooks and downloaded Terraform ZIPs.

## Security Notes
RVTools exports can contain sensitive infrastructure inventory, network, host, cluster, operating system, and application-planning data.

Before shared deployment:
- Require authenticated access.
- Use HTTPS.
- Restrict the app to an internal network or approved user group.
- Prefer private endpoint visibility or an internal platform when customer inventory data is uploaded.
- Avoid committing RVTools workbooks, generated ZIPs, `.env` files, or Streamlit secrets.
- Decide whether uploaded workbooks and generated packages are allowed to persist outside the user session.
- Decide whether generated business case CSVs, planning-state JSON files, and Terraform ZIP bundles may be downloaded to analyst workstations.
- Define retention expectations for browser downloads, exported handoff packages, and any platform logs.
- Do not store IBM Cloud API keys in the image. Use approved environment variable, secret, or workload identity patterns if live catalog access is needed.
- Treat generated Terraform and handoff files as sensitive migration planning artifacts.

The included `.dockerignore` and `.ceignore` exclude common local secrets, virtual environments, Terraform state files, generated ZIPs, logs, and workbook inputs from container builds and Code Engine source uploads. These ignore files reduce accidental packaging risk; they do not replace source-control review or secret scanning.

## Static HTML Clarification
A static HTML page can be useful as a landing page, internal launch page, or documentation wrapper. It cannot run this app by itself because the current application depends on Python for:
- parsing RVTools XLSX workbooks,
- applying readiness and sizing logic,
- managing Streamlit session state,
- rendering Terraform and handoff files,
- creating downloadable ZIP packages.

Keeping Streamlit as the served app is the lowest-risk path. A separate HTML/React frontend plus API backend would be a new product architecture, not a packaging change.

## Deployment Files
- `Dockerfile` builds the Streamlit container and starts `app.py`.
- `.dockerignore` keeps local artifacts and sensitive input/output files out of the image.
- `.ceignore` keeps local artifacts and sensitive input/output files out of Code Engine source uploads.
- `.streamlit/config.toml` disables usage stats and sets the app to run headless on `0.0.0.0`.
