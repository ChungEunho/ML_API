#!/usr/bin/env bash
set -euo pipefail

# Config
SERVER_URL=${SERVER_URL:-http://localhost:8000}
IMAGE_PATH="${1:-/Users/eunho/Desktop/DGIST/Projects/MLAPI_dev/test_input/bus.jpg}"
OUT_JSON=${OUT_JSON:-/tmp/predict.json}
OUT_IMG=${OUT_IMG:-/tmp/result.jpg}

echo "[1/4] POST /predict with file=${IMAGE_PATH}"
if [ ! -f "${IMAGE_PATH}" ]; then
  echo "Error: IMAGE_PATH not found: ${IMAGE_PATH}" >&2
  exit 1
fi

curl -s -X POST \
  -F "file=@${IMAGE_PATH}" \
  "${SERVER_URL}/predict/" | tee "${OUT_JSON}" >/dev/null

# Extract image_url (prefer jq if available, else Python)
echo "[2/4] Extract image_url from response JSON"
if command -v jq >/dev/null 2>&1; then
  IMAGE_URL=$(jq -r '.image_url' "${OUT_JSON}")
else
  IMAGE_URL=$(python3 - "$OUT_JSON" <<'PY'
import json,sys
with open(sys.argv[1]) as f:
    d=json.load(f)
print(d.get('image_url',''))
PY
)
fi

if [ -z "${IMAGE_URL}" ] || [ "${IMAGE_URL}" = "null" ]; then
  echo "Error: Failed to extract image_url from ${OUT_JSON}" >&2
  cat "${OUT_JSON}" >&2
  exit 1
fi

echo "[3/4] GET ${SERVER_URL}${IMAGE_URL} -> ${OUT_IMG}"
HTTP_CODE=$(curl -s -o "${OUT_IMG}" -w "%{http_code}" "${SERVER_URL}${IMAGE_URL}")
echo "HTTP ${HTTP_CODE}"

# The file is scheduled for deletion via BackgroundTasks; a short wait can help ensure it is gone.
sleep 0.2 || true

echo "[4/4] Second GET should be 404"
HTTP_CODE2=$(curl -s -o /dev/null -w "%{http_code}" "${SERVER_URL}${IMAGE_URL}")
echo "HTTP ${HTTP_CODE2}"

if [ "${HTTP_CODE}" != "200" ]; then
  echo "First GET failed with HTTP ${HTTP_CODE}" >&2
  exit 1
fi

if [ "${HTTP_CODE2}" != "404" ]; then
  echo "Warning: Second GET expected 404 but got ${HTTP_CODE2}" >&2
fi

echo "Done. Saved image to ${OUT_IMG}"