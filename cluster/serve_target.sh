#!/bin/bash
# Launch the TARGET vLLM server: the model under test ($TARGET_MODEL, swept per array task).
# A Qwen3 / R1-distill target reasons via its own chat template; the driver toggles Qwen3
# thinking through chat_template_kwargs (TARGET_THINKING_PARAM=chat_template, set in env.sh).
# CUDA_VISIBLE_DEVICES is set by the caller and must list TARGET_TP GPUs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"

exec python -m vllm.entrypoints.openai.api_server \
  --model "$TARGET_MODEL" \
  --served-model-name "$TARGET_MODEL" \
  --host 0.0.0.0 --port "$TARGET_PORT" \
  --tensor-parallel-size "$TARGET_TP" \
  --max-model-len "$TARGET_MAX_LEN"
