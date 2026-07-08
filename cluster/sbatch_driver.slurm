#!/bin/bash
# ===========================================================================
# Single-node driver: launch the three role servers (judge / proxy / target),
# wait until all are ready, then run the experiment driver for one target model.
# Submit as an ARRAY job — one array task per line in cluster/target_models.txt:
#
#     N=$(grep -vcE '^\s*(#|$)' cluster/target_models.txt)
#     sbatch --array=0-$((N-1)) cluster/sbatch_driver.slurm
#
# Each array task is self-contained: it spins up its own judge+proxy+target on
# one node. That re-loads the judge/proxy per target (simple + robust, no
# cross-job coordination). If that is too costly, run judge+proxy as separate
# long-lived jobs and point JUDGE_BASE_URL/PROXY_BASE_URL at them instead.
# ===========================================================================

# ---- SLURM headers (EDIT the placeholders) --------------------------------
#SBATCH --job-name=syco-sweep
#SBATCH --account=ACCOUNT
#SBATCH --partition=PARTITION
#SBATCH --time=TIME                  # e.g. 24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:TYPE:N            # N must be >= JUDGE_TP + PROXY_TP + TARGET_TP (see env.sh)
#SBATCH --output=cluster/logs/%x_%A_%a.out
#SBATCH --error=cluster/logs/%x_%A_%a.err

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"
mkdir -p cluster/logs

# Which experiment(s) to run: fp | ue | both
: "${EXPERIMENT:=both}"

# ---- Pick this task's target model from the list (skip comments/blanks) ----
mapfile -t MODELS < <(grep -vE '^\s*(#|$)' cluster/target_models.txt)
IDX="${SLURM_ARRAY_TASK_ID:-0}"
if [ "$IDX" -ge "${#MODELS[@]}" ]; then
  echo "Array index $IDX out of range (${#MODELS[@]} models listed)" >&2
  exit 1
fi
export TARGET_MODEL="${MODELS[$IDX]}"     # export BEFORE sourcing env.sh so it wins
echo "[driver] array task $IDX -> TARGET_MODEL=$TARGET_MODEL"

# ---- Conda + env ----------------------------------------------------------
source cluster/env.sh
# module load anaconda3        # <- EDIT: load your cluster's conda module if needed
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# ---- GPU pinning: hand each server a disjoint slice of the node's GPUs -----
gpu=0
JUDGE_GPUS=$(seq -s, "$gpu" $((gpu + JUDGE_TP - 1)));   gpu=$((gpu + JUDGE_TP))
PROXY_GPUS=$(seq -s, "$gpu" $((gpu + PROXY_TP - 1)));   gpu=$((gpu + PROXY_TP))
TARGET_GPUS=$(seq -s, "$gpu" $((gpu + TARGET_TP - 1))); gpu=$((gpu + TARGET_TP))
echo "[driver] GPUs -> judge:[$JUDGE_GPUS] proxy:[$PROXY_GPUS] target:[$TARGET_GPUS] (need $gpu total)"

# ---- Launch the three servers in the background ---------------------------
CUDA_VISIBLE_DEVICES="$JUDGE_GPUS"  bash cluster/serve_judge.sh  > "cluster/logs/judge_${SLURM_ARRAY_TASK_ID:-0}.log"  2>&1 & JUDGE_PID=$!
CUDA_VISIBLE_DEVICES="$PROXY_GPUS"  bash cluster/serve_proxy.sh  > "cluster/logs/proxy_${SLURM_ARRAY_TASK_ID:-0}.log"  2>&1 & PROXY_PID=$!
CUDA_VISIBLE_DEVICES="$TARGET_GPUS" bash cluster/serve_target.sh > "cluster/logs/target_${SLURM_ARRAY_TASK_ID:-0}.log" 2>&1 & TARGET_PID=$!

# Always tear the servers down when the driver exits (success, failure, or scancel).
cleanup() { echo "[driver] stopping servers"; kill "$JUDGE_PID" "$PROXY_PID" "$TARGET_PID" 2>/dev/null || true; }
trap cleanup EXIT

# ---- Wait for readiness (weights loaded) ----------------------------------
bash cluster/wait_ready.sh

# ---- Run the experiment driver(s) -----------------------------------------
# Sanitize the target id for a per-target output subfolder (avoid '/' in paths).
SAFE_TARGET="${TARGET_MODEL//\//__}"
RUN_ARGS=( --target-model "$TARGET_MODEL" --max-turns 99 )   # EDIT extra flags as needed

if [ "$EXPERIMENT" = "fp" ] || [ "$EXPERIMENT" = "both" ]; then
  echo "[driver] === false_presuppositions: $TARGET_MODEL ==="
  python false_presuppositions/false_presuppositions.py \
    "${RUN_ARGS[@]}" \
    --output-dir "false_presuppositions/outputs/cluster/${SAFE_TARGET}"
fi

if [ "$EXPERIMENT" = "ue" ] || [ "$EXPERIMENT" = "both" ]; then
  echo "[driver] === unethical_settings: $TARGET_MODEL ==="
  python unethical_setting/unethical_settings.py \
    "${RUN_ARGS[@]}" \
    --output-dir "unethical_setting/outputs/cluster/${SAFE_TARGET}"
fi

echo "[driver] done: $TARGET_MODEL"
