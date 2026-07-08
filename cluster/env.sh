# shellcheck shell=bash
# ---------------------------------------------------------------------------
# Cluster environment for the sycophancy experiments — one vLLM server per role.
# Source this from the serve_*.sh scripts and from the sbatch driver:
#     source cluster/env.sh
#
# Every value uses ${VAR:=default}, so anything exported before sourcing (e.g.
# TARGET_MODEL set per SLURM array task) wins over these defaults.
# ---------------------------------------------------------------------------

# ---- Conda / Python env (EDIT) -------------------------------------------
: "${CONDA_ENV:=sycophancy}"          # conda env that has: vllm, openai, tenacity, python-dotenv

# ---- Model ids (must match --served-model-name in the serve_*.sh) --------
: "${JUDGE_MODEL:=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B}"   # R1-distill judge
: "${PROXY_MODEL:=Qwen/Qwen2.5-7B-Instruct}"                   # Qwen chat proxy
: "${TARGET_MODEL:=Qwen/Qwen2.5-7B-Instruct}"                  # overridden per array task

# ---- Ports (localhost; no cross-node discovery needed) -------------------
: "${JUDGE_PORT:=8001}"
: "${PROXY_PORT:=8002}"
: "${TARGET_PORT:=8003}"

# ---- Tensor-parallel size per role (= #GPUs that role's server uses) ------
# Keep these consistent with the CUDA_VISIBLE_DEVICES pinning in the sbatch:
# the number of GPUs handed to each server must equal its *_TP.
: "${JUDGE_TP:=2}"     # 32B judge: 2 GPUs is typical
: "${PROXY_TP:=1}"     # 7B proxy: 1 GPU
: "${TARGET_TP:=1}"    # bump for large targets (e.g. 32B → 2)

# ---- Max context length per role -----------------------------------------
: "${JUDGE_MAX_LEN:=16384}"
: "${PROXY_MAX_LEN:=16384}"
: "${TARGET_MAX_LEN:=16384}"

# ---- Derived base URLs the Python driver reads ---------------------------
# These names are exactly what the experiment modules look up.
export JUDGE_BASE_URL="http://127.0.0.1:${JUDGE_PORT}/v1"
export PROXY_BASE_URL="http://127.0.0.1:${PROXY_PORT}/v1"
export TARGET_BASE_URL="http://127.0.0.1:${TARGET_PORT}/v1"
export JUDGE_MODEL PROXY_MODEL TARGET_MODEL

# Local vLLM needs no auth; the driver falls back to "EMPTY" on its own, but make
# it explicit so nothing tries the hosted DeepSeek path.
export JUDGE_API_KEY="${JUDGE_API_KEY:-EMPTY}"
export PROXY_API_KEY="${PROXY_API_KEY:-EMPTY}"
export TARGET_API_KEY="${TARGET_API_KEY:-EMPTY}"

# Local vLLM targets must deliver Qwen3's thinking toggle via chat_template_kwargs.
export TARGET_THINKING_PARAM="${TARGET_THINKING_PARAM:-chat_template}"

export CONDA_ENV JUDGE_PORT PROXY_PORT TARGET_PORT \
       JUDGE_TP PROXY_TP TARGET_TP JUDGE_MAX_LEN PROXY_MAX_LEN TARGET_MAX_LEN
