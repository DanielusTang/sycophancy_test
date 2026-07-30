#!/bin/bash
# ===========================================================================
# Unethical-setting (stereotype-pressure) API pipeline on Olmo3-7B variants
# (base/instruct/think).
#   TARGET = local vLLM server (OpenAI-compatible, pipeline provider "openai")
#   PROXY  = claude-sonnet-5 via the Anthropic API
#   JUDGE  = claude-sonnet-5 via the Anthropic API
#
# One SLURM array task per line in cluster/olmo_variants.txt:
#
#     sbatch --array=0-2 cluster/sbatch_ue_olmo.slurm
#
# Smoke test (1 case, 3 turns, short walltime):
#
#     sbatch --array=0-2 --time=01:00:00 \
#       --export=ALL,UE_EXTRA_FLAGS="--limit 1 --max-turns 3" \
#       cluster/sbatch_ue_olmo.slurm
#
# Requires: repo-root .env with CLUDE_API_KEY (or ANTHROPIC_API_KEY), conda env
# with requirements.txt + vllm, and outbound HTTPS to api.anthropic.com from
# compute nodes. Do NOT source cluster/env.sh here — it would repoint the judge
# (JUDGE_MODEL) at a local server.
# ===========================================================================

# ---- SLURM headers (EDIT the placeholders) --------------------------------
#SBATCH --job-name=ue-olmo3
#SBATCH --account=ACCOUNT
#SBATCH --partition=PARTITION
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=cluster/logs/%x_%A_%a.out
#SBATCH --error=cluster/logs/%x_%A_%a.err

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"
mkdir -p cluster/logs

# ---- Tunables (env-overridable at sbatch time via --export) ---------------
: "${CONDA_ENV:=sycophancy}"
: "${TARGET_PORT:=8003}"
: "${TARGET_MAX_LEN:=32768}"      # Olmo3 supports 64K; 32K covers long dialogues
: "${MAX_TURNS:=99}"
: "${WAIT_TIMEOUT:=1200}"         # seconds to wait for vLLM weight loading
: "${HF_HOME:=${SCRATCH:-$HOME}/hf_cache}"   # pre-download weights here (login node)
export HF_HOME

# ---- Pick this task's variant from the map (skip comments/blanks) ---------
mapfile -t LINES < <(grep -vE '^\s*(#|$)' "$HERE/olmo_variants.txt")
IDX="${SLURM_ARRAY_TASK_ID:-0}"
if [ "$IDX" -ge "${#LINES[@]}" ]; then
  echo "Array index $IDX out of range (${#LINES[@]} variants listed)" >&2
  exit 1
fi
IFS='|' read -r MODEL VARIANT EXTRA_ARGS THINK_FLAG <<< "${LINES[$IDX]}"
EXTRA_ARGS="${EXTRA_ARGS//CLUSTER_DIR/$HERE}"
echo "[ue-olmo] task $IDX -> model=$MODEL variant=$VARIANT vllm_extra='$EXTRA_ARGS' think=$THINK_FLAG"

# ---- Conda ----------------------------------------------------------------
# module load Anaconda3        # <- EDIT: load your cluster's conda module if needed
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# ---- Preflight 1: Anthropic key present + egress to api.anthropic.com -----
# Mirrors the pipeline's own key resolution (.env at repo root, CLUDE_API_KEY
# spelling included). Fails fast so we don't burn GPU hours with no proxy/judge.
python - <<'PY'
import os, sys
from dotenv import load_dotenv
load_dotenv(".env")
key = os.getenv("CLUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
if not key:
    sys.exit("PREFLIGHT FAIL: no Anthropic key in .env (CLUDE_API_KEY/ANTHROPIC_API_KEY)")
import anthropic
m = anthropic.Anthropic(api_key=key).models.retrieve("claude-sonnet-5")
print(f"PREFLIGHT OK: reached api.anthropic.com, model={m.id}")
PY

# ---- Serve the Olmo target on vLLM (single GPU, TP=1) ---------------------
VLLM_LOG="cluster/logs/vllm_ue_${VARIANT}_${SLURM_ARRAY_TASK_ID:-0}.log"
# shellcheck disable=SC2086   # EXTRA_ARGS is intentionally word-split
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --served-model-name "$MODEL" \
  --host 127.0.0.1 --port "$TARGET_PORT" \
  --tensor-parallel-size 1 \
  --max-model-len "$TARGET_MAX_LEN" \
  $EXTRA_ARGS \
  > "$VLLM_LOG" 2>&1 & VLLM_PID=$!

cleanup() { echo "[ue-olmo] stopping vLLM"; kill "$VLLM_PID" 2>/dev/null || true; }
trap cleanup EXIT

# ---- Preflight 2: vLLM readiness (200 on /v1/models = weights loaded) -----
deadline=$(( $(date +%s) + WAIT_TIMEOUT ))
until curl -sf "http://127.0.0.1:${TARGET_PORT}/v1/models" >/dev/null; do
  if ! kill -0 "$VLLM_PID" 2>/dev/null; then
    echo "[ue-olmo] vLLM died during startup; see $VLLM_LOG" >&2
    exit 1
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "[ue-olmo] vLLM readiness timeout after ${WAIT_TIMEOUT}s; see $VLLM_LOG" >&2
    exit 1
  fi
  sleep 5
done
echo "[ue-olmo] vLLM ready."

# ---- Wire the pipeline's provider-"openai" target at the local server -----
export OPENAI_BASE_URL="http://127.0.0.1:${TARGET_PORT}/v1"
export OPENAI_API_KEY="EMPTY"
# Extra output headroom for the think variant's long chain-of-thought
# (consumed by TargetAgent's provider-openai branch):
if [ "$VARIANT" = "olmo3_7b_think" ]; then
  export TARGET_MAX_TOKENS=8192
fi

# ---- Run ------------------------------------------------------------------
OUTDIR="unethical_setting/outputs/${VARIANT}"
echo "[ue-olmo] === unethical_setting ($VARIANT): $MODEL -> $OUTDIR ==="
# shellcheck disable=SC2086   # UE_EXTRA_FLAGS is intentionally word-split
python unethical_setting/unethical_main.py \
  --mode naturalistic \
  --target-provider openai --target-model "$MODEL" "$THINK_FLAG" \
  --proxy-provider anthropic --model claude-sonnet-5 \
  --judge-provider anthropic --judge-model claude-sonnet-5 \
  --max-turns "$MAX_TURNS" \
  --output-dir "$OUTDIR" \
  ${UE_EXTRA_FLAGS:-}

echo "[ue-olmo] done: $VARIANT -> $OUTDIR"
