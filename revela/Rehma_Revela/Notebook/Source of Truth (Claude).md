# Source of Truth (Claude) — Revela Tickets

> Synced from GitHub issues. Last sync: 2026-05-18
> Source: https://github.com/romanpoluden/revela/issues

## Active (P0, in flight on Rehma's branch)

- **#142 — D4.6 — Evaluate BCN+MNH CNN on frozen BCN20000 test set** — P0 (next up; checkpoint ready at `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth`)

## Next up (unblocked, not started)

- #143 — D4.7 — Update decision log and project context for MNH augmentation track — P0 (blocked on #142 results)
- #123 — D3.7 — Update inference and app schema for dermoscopic cancer-risk model — P1 (assignee: romanpoluden)
- #108 — Prepare benchmark plan vs ChatGPT and Claude — P1

## Backlog (P1/P2, not urgent)

- #132 — V2.9 — Add source-aware and class-aware sampling for clinical v2 training — P1
- #133 — V2.10 — Build high-confidence SCIN clinical dataset variant — P1
- #131 — V2.8 — Analyze clinical v2 errors by source, class, and raw label — P0 (assignee: izssa; branch: v2.8-clinical-error-analysis)
- #49 — F1.1 — Implement config-driven model loading for inference — P0 (assignee: izssa; branch: f1.1-config-driven-model-loader)
- #53 — F1.5 — Define inference response schema — P0 (assignee: romanpoluden)
- #51 — F1.3 — Convert probabilities to top-3 predictions — P0 (assignee: romanpoluden)
- Week 3 frontend/demo/safety series (#55–#87) — P0/P1 — unassigned, not started
- Week 4 LLM integration series (#88–#98) — P0/P1 — unassigned, not started
- Inference stubs (#31, #34, #50, #52, #54) — P0/P1 — unassigned/stale

## Recently closed (last 30 days)

### MNH augmentation track (D4.1–D4.5) — closed in last 24h

- #141 — D4.5 — Retrain cancer-risk CNN on BCN+MNH merged dataset — closed 2026-05-18 (val_macro_f1=0.6768, val_acc=74.16%, best epoch 6/10)
- #140 — D4.4 — Merge filtered MNH with BCN20000 training data and create splits — closed 2026-05-17 (train=21,233, val=3,619; lesion-grouped, BCN test untouched)
- #139 — D4.3 — Map MNH diagnosis labels to cancer-risk taxonomy — closed 2026-05-17 (DEC-009; Mel 4,345 · Nevus 8,050 · Other 105 · NMSC 0)
- #138 — D4.2 — Filter BCN20000 IDs from Mel+Nevus Histo — closed 2026-05-17 (18,133 → 12,500; −5,633 dupes)
- #137 — D4.1 — Download Mel+Nevus Histo dataset — closed 2026-05-17 (18,133 images, 0 corrupt)

### Earlier

- #120 — D3.5 — Evaluate dermoscopic cancer-risk CNN — closed 2026-05-15
- #119 — D3.4 — Retrain dermoscopic CNN with cancer-risk taxonomy — closed 2026-05-15
- #116 — D3.1 — Redefine dermoscopic CNN target as cancer-risk classification — closed 2026-05-15
- #118 — D3.3 — Rebuild BCN20000 processed splits for cancer-risk taxonomy — closed 2026-05-13
- #130 — V2.7 — Evaluate clinical-image CNN on held-out test split — closed 2026-05-12
- #129 — V2.6 — Train clinical-image CNN baseline — closed 2026-05-12
- #128 — D3.1.2 — Update docs and notebook 03 with finalized 4-class cancer-risk taxonomy — closed 2026-05-12
- #125 — V2.5 — Build clinical-image dataset with approved 5-class taxonomy — closed 2026-05-12
- #122 — D3.6 — Assess supplemental dermoscopic cancer datasets — closed 2026-05-12
- #126 — V2.5 — Build clinical-image dataset with approved 5 classes — closed 2026-05-11
- #124 — V2.4 — Count grouped clinical labels across SCIN and Fitzpatrick17k — closed 2026-05-11
- #117 — D3.2 — Create cancer-risk label mapping for BCN20000 — closed 2026-05-11

## Dependency chains (current critical paths)

**Dermoscopic baseline (closed):**
```
#116 ✅ → #117 ✅ → #118 ✅ → #119 ✅ → #120 ✅ → #123 ⬜
```

**MNH augmentation track (D4.x):**
```
#137 ✅ → #138 ✅ → #139 ✅ → #140 ✅ → #141 ✅ → #142 ▶ → #143 ⏸
```

`✅ done  ▶ active  ⏸ blocked  ⬜ not started`

## Trained models on disk

| Model | Train data | Best epoch | Val macro-F1 | Val acc | Checkpoint |
|---|---|---:|---:|---:|---|
| BCN-only baseline (#119) | BCN20000 train 12,352 | 6 | 0.6924 | 70.09% | `models/bcn20000_cancer_risk_effnet_b0/best_model.pth` |
| BCN+MNH augmented (#141) | merged train 21,233 | 6 | 0.6768 | 74.16% | `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` (mirror `models/bcn_mnh_cancer_risk_cnn_epoch6.pth`) |

Both EfficientNet-B0 / ImageNet / 224×224 / batch 16 / AdamW lr=3e-4 wd=0.01 / 10 epochs / inverse-frequency class weights.

## Flags / anomalies

- **#121** may be a duplicate of closed #122 — verify before starting work.
- **#131, #49** are team P0s sitting in Backlog — not assigned to Rehma, but worth tracking.
- **#142 vs #120 comparison rule:** D4.6 must use the same frozen BCN20000 test set as #120 — md5 `a67861586e00812aadf46f2bdb4bc01b`. Hash-assert before evaluating; never re-shuffle or re-split this file.
- **Notebook 12 is guarded against re-execution.** Cells 4 and 5 skip if `training_history.csv` already has ≥10 epochs. If you genuinely want to retrain, delete that file plus `best_model.pth` first.
