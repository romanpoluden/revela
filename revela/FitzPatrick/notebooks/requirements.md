# CLAUDE.md — Revela

> Edit the tech stack and paths if any of this doesn't match the repo. Keep this file under ~5k tokens — it sits in context on every turn.

## Project

Revela is an AI-powered skin disease diagnostic tool. Primary users: dermatology residents and trainees (PGY-1 through IMGs). The system combines a CNN image classifier with an LLM reasoning layer. Output: a top-3 differential diagnosis with calibrated confidence scores and visual feature reasoning. Framing is a **clinical reasoning scaffold, not a diagnostic device**. Solo build, one-month timeline.

## Tech stack

- Python 3.11
- TensorFlow / Keras for the CNN
- FastAPI for the demo web app
- Docker + Docker Compose for packaging
- Jupyter notebooks for EDA only
- Anthropic API (Claude) for the LLM reasoning layer

## Datasets

- **Primary training:** Fitzpatrick17k → `data/fitzpatrick17k/`
- **Evaluation hold-out:** SCIN → `data/scin/`
- **Backup (no approval needed):** HAM10000 → `data/ham10000/`, DDI → `data/ddi/`
- **Awaiting access:** PASSION

Always work from metadata CSVs / `metadata.json`, not from the raw image folders.

## CNN scoped classes

1. Melanoma
2. Benign nevus
3. Eczema / dermatitis
4. Other / unclear
5. (Candidate) BCC — basal cell carcinoma, from ISIC 2019

## Code conventions

- Type hints on every function signature
- Black formatting, line length 100
- Docstrings: one-line summary; args / returns only when non-obvious
- No `from x import *`
- Imports grouped: stdlib, third-party, local
- Source in `src/`, experiments in `notebooks/`, tests in `tests/` mirroring `src/`

---

## Response behavior — token-saving (IMPORTANT)

- **Default to terse.** Skip preamble like "Great question" or "Here's what I'll do." Just do the thing.
- **No lengthy explanations** unless I ask. Code first; brief reasoning only if a non-obvious choice was made.
- **Edits as diffs.** Use `str_replace` / show old → new chunks. Do not rewrite whole files for small changes.
- **New files:** full content is fine.
- **End-of-task summary:** ≤3 bullets — what changed, why, what's next. Nothing more.
- **Don't narrate** as you read files. Read, then answer.
- **Ask before guessing.** If a request is ambiguous or seems wrong-headed, ask one short clarifying question instead of building the wrong thing and burning context.

## Plan mode

For any change touching more than one file, or any new feature, **use plan mode first** (Shift+Tab). Wait for my approval before editing. Fixing a plan is nearly free; fixing a half-built approach is not.

## Reading rules

Do **not** read these — they bloat context and never help:

- `data/*/images/`, `data/*/raw/` (the actual image files)
- `.venv/`, `node_modules/`, `__pycache__/`, `.git/`
- Anything in `archive/` or `old/`

For unfamiliar files, prefer `ls`, `head`, or `wc -l` over reading the whole thing.

## Test output

- Run the most relevant test file first. Run broader tests only after it passes.
- Show failures and the summary line only. Do not dump full passing output.

## Compaction

If `/compact` is invoked, preserve:

- Current dataset paths and active class list
- Model architecture decisions made this session
- Open TODOs and any unresolved bug
- Drop verbose tool outputs and intermediate exploration

## Out of scope for Claude Code

I handle these in Claude.ai chat — don't expand on them here:

- Capstone narrative, slide content, stakeholder framing
- Outreach emails, persona docs, research synthesis
- Strategy and product decisions

This file is for code and infra only.
