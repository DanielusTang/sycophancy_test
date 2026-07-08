#!/bin/bash
# Launch the JUDGE vLLM server: DeepSeek R1-distill with the reasoning parser, so the
# chain-of-thought lands in reasoning_content and `content` is clean JSON for the judge.
# CUDA_VISIBLE_DEVICES is set by the caller (the sbatch) and must list JUDGE_TP GPUs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"

exec python -m vllm.entrypoints.openai.api_server \
  --model "$JUDGE_MODEL" \
  --served-model-name "$JUDGE_MODEL" \
  --host 0.0.0.0 --port "$JUDGE_PORT" \
  --tensor-parallel-size "$JUDGE_TP" \
  --max-model-len "$JUDGE_MAX_LEN" \
  --reasoning-parser deepseek_r1
