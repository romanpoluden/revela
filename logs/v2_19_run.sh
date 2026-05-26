#!/usr/bin/env bash
# V2.19 (issue #160) — train + evaluate baseline regen, staged fine-tune, low-LR fine-tune.
# All on the frozen clinical_v2 split. Fingerprint verified before and after.
set -euo pipefail
cd /Users/rehmaaziz/revela
export PYTORCH_ENABLE_MPS_FALLBACK=1

echo "=== START $(date) ==="
echo "test.csv md5 (before): $(md5 -q data/processed/clinical_v2/test.csv)"

run () {
  local name="$1" cfg="$2" prefix="$3"
  echo; echo "########## TRAIN ${name} $(date) ##########"
  python -m src.model.train --config "${cfg}"
  echo; echo "########## EVAL ${name} $(date) ##########"
  python -m src.model.evaluate_clinical_v2 --config "${cfg}" --output-prefix "${prefix}"
}

run "baseline-regen"   config/clinical_v2_config.yaml                  clinical_v2_baseline_regen
run "staged-finetune"  config/clinical_v2_staged_finetune_config.yaml  clinical_v2_staged_finetune
run "low-lr-finetune"  config/clinical_v2_low_lr_finetune_config.yaml  clinical_v2_low_lr_finetune

echo; echo "test.csv md5 (after):  $(md5 -q data/processed/clinical_v2/test.csv)"
echo "=== DONE $(date) ==="
