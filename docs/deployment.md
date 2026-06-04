# Deployment Guide

This app is a Streamlit/Python application. Users can access it through a web browser, but the app is not a static HTML site because RVTools workbook parsing, readiness logic, pricing logic, session state, Terraform rendering, and ZIP generation run in Python.

## Recommended Deployment Model
For migration team use, deploy the app as a private containerized Streamlit service.

Recommended order:
1. Run locally for individual assessment work.
2. Run the included container image for team validation.
3. Deploy the container to IBM Cloud Code Engine or an internal container platform.

IBM Cloud Code Engine is a good first hosted target because it can run containerized web apps and supports Dockerfile-based source builds. See the IBM Code Engine getting started guide and application workload docs:
- https://cloud.ibm.com/docs/codeengine?topic=codeengine-getting-started
- https://cloud.ibm.com/docs/codeengine?topic=codeengine-application-workloads

Streamlit's Docker deployment guidance is also useful for local and container-platform validation:
- https://docs.streamlit.io/deploy/tutorials/docker

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
The container command honors Code Engine's `PORT` environment variable. If no `PORT` is provided, it defaults to `8501` for local use.

One common Code Engine flow is:

```bash
ibmcloud login
ibmcloud plugin install code-engine
ibmcloud ce project select --name <project-name>
ibmcloud ce application create \
  --name rvtools-to-ibm-cloud \
  --build-source . \
  --port 8501
```

Use the generated application URL to access the Streamlit workbench.

For production or shared-team use, configure access control through the hosting environment, ingress, reverse proxy, or enterprise SSO pattern approved for the deployment. If the app should not be reachable from the public internet, use Code Engine endpoint visibility controls such as `--visibility=private` where appropriate for the network design.

## Security Notes
RVTools exports can contain sensitive infrastructure inventory, network, host, cluster, operating system, and application-planning data.

Before shared deployment:
- Require authenticated access.
- Use HTTPS.
- Restrict the app to an internal network or approved user group.
- Avoid committing RVTools workbooks, generated ZIPs, `.env` files, or Streamlit secrets.
- Decide whether uploaded workbooks and generated packages are allowed to persist outside the user session.
- Treat generated Terraform and handoff files as sensitive migration planning artifacts.

The included `.dockerignore` excludes common local secrets, virtual environments, Terraform state files, generated ZIPs, logs, and workbook inputs from container builds.

## Deployment Files
- `Dockerfile` builds the Streamlit container and starts `app.py`.
- `.dockerignore` keeps local artifacts and sensitive input/output files out of the image.
- `.ceignore` keeps local artifacts and sensitive input/output files out of Code Engine source uploads.
- `.streamlit/config.toml` disables usage stats and sets the app to run headless on `0.0.0.0`.
