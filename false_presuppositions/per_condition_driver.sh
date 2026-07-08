#!/bin/zsh
# Independent per-condition driver: marches one condition through q6..q25
# sequentially (one question at a time for THIS condition), without waiting
# for any other condition. Usage: per_condition_driver.sh <cond> <model> <off|on>
cd /Users/danielus/sycophancy_test/false_presuppositions || exit 1

cond=$1; model=$2; think=$3
extra=()
[ "$think" = "off" ] && extra=(--no-proxy-thinking)

COMMON=(--proxy-provider qwen --judge-provider openai --judge-model gpt-4o \
        --target-provider deepseek --target-model deepseek-v4-pro \
        --max-turns 99 --seed 0 --limit 1)

mkdir -p ablasion_qwen_outputs/$cond
DRV="ablasion_qwen_outputs/driver_${cond}.log"
echo "[$cond] starting q6..q25 at $(date)" >> "$DRV"

for q in {6..25}; do
  start=$((q-1))

  # 1) If a run for this (cond,q) is already alive (e.g. q6 from old barrier
  #    driver), wait for it to finish instead of launching a duplicate.
  while pgrep -f "false_presuppositions_naturalistic.py.*--start ${start} --tag ${cond}" >/dev/null 2>&1; do
    sleep 10
  done

  # 2) If output already exists, it's done — skip relaunch.
  if ls ablasion_qwen_outputs/$cond/sycophancy_strength_naturalistic_q${q}_*.jsonl >/dev/null 2>&1; then
    echo "[$cond] q$q already present, skip at $(date)" >> "$DRV"
    continue
  fi

  # 3) Otherwise launch and wait for just this one.
  echo "[$cond] launching q$q (start=$start) at $(date)" >> "$DRV"
  python3 -u false_presuppositions_naturalistic.py "${COMMON[@]}" "${extra[@]}" \
    --model "$model" --start $start --tag "$cond" \
    --output-dir ablasion_qwen_outputs/$cond \
    > ablasion_qwen_outputs/$cond/run_q${q}.log 2>&1 &
  wait $!
  echo "[$cond] q$q finished at $(date)" >> "$DRV"
done

echo "[$cond] ALL DONE q6..q25 at $(date)" >> "$DRV"
