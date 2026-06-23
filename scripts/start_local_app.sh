#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
APP_URL=${APP_URL:-http://localhost:8501}
STREAMLIT_HEALTH_URL=${STREAMLIT_HEALTH_URL:-${APP_URL}/_stcore/health}
APP_IMAGE=${APP_IMAGE:-rvtools-to-ibm-cloud:local}

cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI was not found."
  echo "Start OrbStack or Docker Desktop, then run this launcher again."
  exit 1
fi

echo "Starting RVTools to IBM Cloud with persistent Postgres storage..."
APP_IMAGE="$APP_IMAGE" docker compose up --build --detach

echo "Waiting for Streamlit at ${APP_URL}..."
attempt=1
while [ "$attempt" -le 60 ]; do
  if curl --fail --silent --show-error "$STREAMLIT_HEALTH_URL" >/dev/null 2>&1; then
    echo "Ready: ${APP_URL}"
    if command -v open >/dev/null 2>&1; then
      open "$APP_URL"
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$APP_URL" >/dev/null 2>&1 || true
    fi
    echo "Use 'docker compose down' from this folder when you want to stop it."
    exit 0
  fi
  echo "Still starting (${attempt}/60)..."
  attempt=$((attempt + 1))
  sleep 2
done

echo "The app did not become healthy in time."
echo "Check logs with: docker compose logs app"
exit 1
