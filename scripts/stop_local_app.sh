#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI was not found."
  echo "Start OrbStack or Docker Desktop if you need to inspect running services."
  exit 1
fi

echo "Stopping RVTools to IBM Cloud local stack..."
docker compose down
echo "Stopped. Persistent database and artifact volumes were kept."
echo "Use 'docker compose down --volumes' only when you intentionally want to erase saved projects."
