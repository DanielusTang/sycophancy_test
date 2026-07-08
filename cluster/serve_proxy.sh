#!/bin/bash
# Launch the PROXY vLLM server: the Qwen chat model that plays the pressuring human.
# CUDA_VISIBLE_DEVICES is set by the caller and must list PROXY_TP GPUs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"

exec python -m vllm.entrypoints.openai.api_server \
  --model "$PROXY_MODEL" \
  --served-model-name "$PROXY_MODEL" \
  --host 0.0.0.0 --port "$PROXY_PORT" \
  --tensor-parallel-size "$PROXY_TP" \
  --max-model-len "$PROXY_MAX_LEN"
