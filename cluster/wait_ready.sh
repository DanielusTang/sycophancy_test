#!/bin/bash
# Block until all three vLLM servers answer GET /v1/models with HTTP 200. A server returns
# 200 only after its weights finish loading, so this is the correct readiness signal — a
# 32B judge can take several minutes. Fails (exit 1) after WAIT_TIMEOUT seconds.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"

: "${WAIT_TIMEOUT:=1800}"   # overall budget, seconds
: "${WAIT_INTERVAL:=5}"

deadline=$(( $(date +%s) + WAIT_TIMEOUT ))
for pair in "judge ${JUDGE_BASE_URL}" "proxy ${PROXY_BASE_URL}" "target ${TARGET_BASE_URL}"; do
  role=${pair%% *}
  url=${pair#* }
  echo "[wait_ready] waiting for ${role} at ${url}/models ..."
  until curl -sf "${url%/}/models" >/dev/null 2>&1; do
    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "[wait_ready] TIMEOUT after ${WAIT_TIMEOUT}s waiting for ${role} (${url})" >&2
      exit 1
    fi
    sleep "$WAIT_INTERVAL"
  done
  echo "[wait_ready] ${role} ready."
done
echo "[wait_ready] all servers ready."
