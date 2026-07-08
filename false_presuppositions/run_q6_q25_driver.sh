#!/bin/zsh
# Sequential overnight driver: for each question q in 6..25, launch all 4
# conditions CONCURRENTLY, wait for all 4 to finish, then move to next q.
# Concurrency is bounded at 4 (one per condition) to avoid rate limits.

cd /Users/danielus/sycophancy_test/false_presuppositions || exit 1

COMMON=(--proxy-provider qwen --judge-provider openai --judge-model gpt-4o \
        --target-provider deepseek --target-model deepseek-v4-pro \
        --max-turns 99 --seed 0 --limit 1)

for cond in qwen8b_off qwen8b_on qwen235b_off qwen235b_on; do
  mkdir -p ablasion_qwen_outputs/$cond
done

DRV="ablasion_qwen_outputs/driver_q6_q25.log"
echo "[driver] starting q6..q25 at $(date)" > "$DRV"

for q in {6..25}; do
  start=$((q-1))
  echo "[driver] ===== question q$q (start=$start) launching 4 conditions =====" >> "$DRV"

  python3 -u false_presuppositions_naturalistic.py "${COMMON[@]}" \
    --model qwen3-8b --no-proxy-thinking --start $start --tag qwen8b_off \
    --output-dir ablasion_qwen_outputs/qwen8b_off \
    > ablasion_qwen_outputs/qwen8b_off/run_q${q}.log 2>&1 &
  p1=$!

  python3 -u false_presuppositions_naturalistic.py "${COMMON[@]}" \
    --model qwen3-8b --start $start --tag qwen8b_on \
    --output-dir ablasion_qwen_outputs/qwen8b_on \
    > ablasion_qwen_outputs/qwen8b_on/run_q${q}.log 2>&1 &
  p2=$!

  python3 -u false_presuppositions_naturalistic.py "${COMMON[@]}" \
    --model qwen3-235b-a22b --no-proxy-thinking --start $start --tag qwen235b_off \
    --output-dir ablasion_qwen_outputs/qwen235b_off \
    > ablasion_qwen_outputs/qwen235b_off/run_q${q}.log 2>&1 &
  p3=$!

  python3 -u false_presuppositions_naturalistic.py "${COMMON[@]}" \
    --model qwen3-235b-a22b --start $start --tag qwen235b_on \
    --output-dir ablasion_qwen_outputs/qwen235b_on \
    > ablasion_qwen_outputs/qwen235b_on/run_q${q}.log 2>&1 &
  p4=$!

  echo "[driver] q$q pids: off8b=$p1 on8b=$p2 off235=$p3 on235=$p4 ; waiting..." >> "$DRV"
  wait $p1 $p2 $p3 $p4
  echo "[driver] q$q all 4 finished at $(date)" >> "$DRV"
done

echo "[driver] ALL DONE q6..q25 at $(date)" >> "$DRV"
