#!/usr/bin/env bash
# Upload pipeline code to the workspace and create/update the refresh job.
#   pipeline/deploy.sh <profile> <catalog> <schema> <since YYYY-MM-DD>
# Workspace-specific values are passed in, never committed.
set -euo pipefail
PROFILE=$1 CATALOG=$2 SCHEMA=$3 SINCE=$4
ME=$(databricks current-user me -p "$PROFILE" -o json | jq -r .userName)
WS_ROOT="/Workspace/Users/$ME/databricks-training"
WS_DIR="$WS_ROOT/pipeline"
HERE=$(cd "$(dirname "$0")" && pwd)

databricks workspace mkdirs "$WS_DIR" -p "$PROFILE"
for f in sources.py collect.py classify.py; do
  databricks workspace import "$WS_DIR/$f" --file "$HERE/$f" --format AUTO --overwrite -p "$PROFILE"
done
databricks workspace import "$WS_ROOT/CLAUDE.md" --file "$HERE/../CLAUDE.md" --format AUTO --overwrite -p "$PROFILE"

RENDERED=$(mktemp -t training-job).json
CATALOG=$CATALOG SCHEMA=$SCHEMA SINCE=$SINCE WS_DIR=$WS_DIR WS_ROOT=$WS_ROOT \
  envsubst '${CATALOG} ${SCHEMA} ${SINCE} ${WS_DIR} ${WS_ROOT}' < "$HERE/job.template.json" > "$RENDERED"

JOB_ID=$(databricks jobs list --name training-content-refresh -p "$PROFILE" -o json | jq -r '.[0].job_id // empty')
if [[ -z "$JOB_ID" ]]; then
  databricks jobs create --json @"$RENDERED" -p "$PROFILE" -o json | jq -r '"created job_id=\(.job_id)"'
else
  # reset replaces settings wholesale — tasks added in the UI (Genie Code, publish) would be dropped.
  echo "job exists (job_id=$JOB_ID); not overwriting. Code files were updated." >&2
fi
rm -f "$RENDERED"
