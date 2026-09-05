#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODEL_FILE="datamodel_demo/app1/models.py"
SCHEMA_FILE="SGBC_data_model.sql"

if ! docker compose ps --status running --services | grep -qx "web"; then
    echo "The web service is not running. Start it with: docker compose up -d --build" >&2
    exit 1
fi

mapfile -t tables < <(sed -n 's/^CREATE TABLE `\([^`]*\)`.*/\1/p' "$SCHEMA_FILE")

if [[ ${#tables[@]} -eq 0 ]]; then
    echo "No CREATE TABLE statements found in $SCHEMA_FILE" >&2
    exit 1
fi

echo "Generating Django models for ${#tables[@]} schema tables..."
docker compose exec -T web python manage.py inspectdb "${tables[@]}" > "$MODEL_FILE"

echo "Running Django checks..."
docker compose exec web python manage.py check

echo "Generated $MODEL_FILE"
