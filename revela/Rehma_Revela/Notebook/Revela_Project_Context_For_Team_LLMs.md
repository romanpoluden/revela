# Revela — Project Context for Team Collaboration

## Purpose of this document

This file gives team members and their LLM assistants enough context to collaborate on the Revela capstone project without re-reading the whole chat history. It summarizes the product concept, research findings, current MVP direction, dataset findings, technical scope, success metrics, risks, and next decisions.

Use this as the shared context file when asking an AI assistant to help with dataset search, model planning, user stories, technical breakdown, GitHub tickets, documentation, or prototype design.

---

# 1. Product Summary

## Product name

**Revela**

## Current positioning

Revela is an **AI-powered dermatology training aid** for dermatology residents and trainees.

It is **not** a diagnostic tool, not a patient-facing self-diagnosis product, and not intended for clinical decision-making.

The product should be framed as a **clinical reasoning scaffold** or **educational case-review assistant**.

## Target audience

Primary users:

- Dermatology residents
- Early-career dermatology trainees
- Medical learners practicing visual differential diagnosis

Secondary stakeholders:

- Dermatology educators
- Residency program leads
- Clinical supervisors
- Medical schools or training hospitals

Not primary users for the MVP:

- Patients
- Ordinary consumers
- General practitioners
- Nurses
- Community health workers
- Hospitals using it for live clinical decisions

## Core problem

Dermatology trainees need more structured, feedback-rich practice for visual diagnostic reasoning, especially across diverse skin presentations and under conditions of uncertainty.

Existing learning often depends on fragmented resources, variable supervisor feedback, and limited exposure to diverse skin tones.

## Product mechanism

A trainee uploads a skin-condition image. Revela returns a **CNN-generated top-3 differential classification** with confidence scores, an uncertainty indicator, structured visual-feature reasoning, and safety/fairness limitations.

If Week 4 extension is completed, an LLM may generate structured educational explanations from the CNN output. The LLM should **not** classify the image and should **not** provide medical diagnosis or treatment advice.

---

# 2. Product Hypothesis

## Core MVP hypothesis

> If dermatology residents can upload a skin-condition image and receive a CNN-generated top-3 differential with confidence scores, uncertainty indicators, and educational visual-feature reasoning, they will perceive Revela as useful and trustworthy for practicing visual diagnostic reasoning.

## What this tests

The MVP tests whether users value:

- Top-3 differential instead of one predicted answer
- Confidence scores instead of black-box output
- Uncertainty indicator instead of false certainty
- Structured visual cues instead of unsupported classification
- Educational positioning instead of diagnostic claims
- Transparent model/data limitations

## What would support the hypothesis

The hypothesis is supported if:

- At least 70% of test users rate Revela as useful for learning visual diagnostic reasoning.
- Users prefer top-3 differential output over single-label output.
- Users say confidence and uncertainty help them interpret the result.
- Users understand Revela is educational, not diagnostic.
- Users find visual-feature reasoning useful.

## What would weaken or reject it

The hypothesis is weakened if:

- Users do not trust the CNN output.
- Users find confidence scores confusing.
- Users still interpret the tool as diagnostic.
- Users say reasoning is too generic.
- Users would not use it for training, case review, or teaching.
- Model output is too poor to be educationally credible.

---

# 3. User Research Findings

Research was based on simulated clinical-style persona interviews with three users:

1. **Prof. Anika Shah** — academic dermatologist and residency teaching lead
2. **Dr. Lena Hoffmann** — practicing clinician / junior learner mindset
3. **Dr. Marco Bianchi** — senior dermatology resident

## Key findings

### Strong rejection of diagnosis framing

All participants showed low trust in AI diagnosis. Revela should not be positioned as a diagnostic tool.

Better framing:

> AI clinical reasoning scaffold for dermatology education and case review.

### Top-3 differential is mandatory

Single diagnosis output was strongly rejected. Dermatology is differential-based. A single answer implies false certainty.

Required output:

- Ranked top-3 differential suggestions
- Confidence score for each suggestion
- Clear uncertainty representation

### Uncertainty representation is mandatory

Users need confidence and uncertainty information to safely interpret output.

Required:

- Confidence percentage per class
- Low / medium / high uncertainty label
- Explanation that model confidence is not clinical certainty

### Visual-feature reasoning is mandatory

Users need to understand which visible image features support the output.

Examples:

- Asymmetry
- Border irregularity
- Color variation
- Uneven pigmentation
- Scaling
- Redness/inflammation
- Diffuse vs localized pattern

For the MVP, this can be template-based. A real heatmap/Grad-CAM is future or stretch.

### Skin-tone fairness matters

All personas treated skin-tone fairness as a safety and trust issue, not an optional ethics feature.

However, the current inspected datasets often lack reliable skin-tone metadata. Therefore the MVP should not claim fairness unless evaluated properly.

Minimum responsible approach:

- Add skin-tone/dataset reliability note in UI.
- Search for datasets with darker skin representation.
- Use datasets with Fitzpatrick or Monk skin-tone metadata where possible.
- Do not manually label skin tone casually.
- Do not claim the model works equally across skin tones unless tested.

### Workflow fit

Revela should be designed for:

- Training
- Post-clinic review
- Case preparation
- Teaching sessions
- Board/exam preparation

It should **not** be designed for under-2-minute live outpatient decision-making in the MVP.

---

# 4. Personas and Jobs-to-be-Done

## Persona 1 — First-Year Dermatology Resident

Needs a private, safe environment to practice visual differential diagnosis.

Main JTBD:

> When I see a lesion or rash I cannot confidently identify, I want to practice building a structured differential so that I can become more confident before discussing cases with senior doctors.

Important features:

- Upload image
- Top-3 differential
- Confidence scores
- Visual-feature reasoning
- Suggested learning questions
- Safety and uncertainty notes

## Persona 2 — Senior Dermatology Resident

Needs realistic image-based cases to sharpen reasoning and prepare for exams or teaching.

Main JTBD:

> When I prepare for exams or complex case discussions, I want to challenge my diagnostic reasoning with realistic image-based cases so that I can defend my reasoning under pressure.

Important features:

- Top-3 differential
- Confidence distribution
- Uncertainty bucket
- Visual reasoning
- Alternative explanations
- High-quality model transparency

## Persona 3 — Dermatology Educator

Needs structured teaching material and a way to teach responsible AI use.

Main JTBD:

> When I design teaching sessions, I want structured, diverse, image-based reasoning practice so that residents improve differential thinking while learning AI limitations responsibly.

Important features:

- Educational disclaimer
- Top-3 differential
- Structured reasoning
- Suggested learning questions
- Model/dataset transparency
- Skin-tone reliability note
- Future educator review flow

---

# 5. MVP Scope

## Current MVP direction

The MVP should be **CNN-first**.

The team needs to train and present a CNN model plus image classification. LLM integration is useful but should be treated as a **Week 4 extension**, not required for the core 3-week MVP.

## 3-week MVP goal

Build a working dermatology training prototype where a resident uploads a skin lesion image and receives a **CNN-generated top-3 differential classification** with confidence scores, uncertainty indicator, and safety/fairness notes.

## Week 4 extension goal

Add a controlled LLM explanation layer that converts CNN output into structured educational reasoning and suggested learning Q&A.

The LLM must not classify the image. It should only explain the CNN result.

---

# 6. Feature Prioritization

## Must-have for 3-week CNN MVP

- Dataset selection and documentation
- Label mapping to MVP taxonomy
- Image preprocessing pipeline
- CNN classifier training
- Model evaluation
- Top-3 prediction output
- Confidence scores
- Uncertainty bucket
- Upload + preview UI
- Result display UI
- Educational-only disclaimer
- Reliability note about skin tone, image quality, lighting, and dataset coverage
- Model/dataset transparency panel
- README and demo script

## Should-have

- Quiz mode
- Suggested learning Q&A with pre-written answers
- Static class-based reasoning templates
- Simple user feedback form
- Basic skin-tone metadata feasibility report

## Could-have / stretch

- Real skin-tone slice evaluation if metadata supports it
- Grad-CAM / heatmap visual explanation
- External validation dataset
- Deployment
- Better model calibration

## Week 4 extension

- LLM prompt template
- LLM explanation endpoint/function
- Structured JSON output
- Fallback to static templates
- LLM output validation
- LLM safety tests
- Generated Q&A

## Won’t-have for MVP

- Patient self-diagnosis
- Treatment recommendations
- Free-form medical chatbot
- EHR integration
- Accounts / login
- Clinical deployment
- CE/MDR regulatory pathway
- Mobile app
- Educator dashboard
- Resident progress tracking

---

# 7. Recommended MVP Taxonomy

Original idea:

- Melanoma
- Benign nevus
- Eczema / dermatitis
- Other / unclear

Current dataset inspection shows that eczema/dermatitis is not well supported in the inspected datasets.

## Recommended practical taxonomy for first CNN baseline

- Melanoma
- Benign nevus
- Other / unclear

## Alternative if using MILK10k and accepting low sample size

- Melanoma
- Benign nevus
- Inflammatory / infectious
- Other / unclear

Do not call the fourth class “eczema / dermatitis” unless the dataset has reliable eczema or dermatitis labels.

---

# 8. Dataset Findings So Far

## HAM10000

Source: Harvard Dataverse, DOI 10.7910/DVN/DBW86T

Metadata summary:

- 10,015 rows/images
- 7,470 unique lesions
- 8 columns
- Important columns: `lesion_id`, `image_id`, `dx`, `dx_type`, `age`, `sex`, `localization`, `dataset`

Diagnosis distribution:

- `nv` — 6,705
- `mel` — 1,113
- `bkl` — 1,099
- `bcc` — 514
- `akiec` — 327
- `vasc` — 142
- `df` — 115

Main strengths:

- Good benchmark dataset
- Good for melanoma / benign nevus / other pigmented lesion baseline
- Has lesion IDs, so grouped split by lesion is possible

Limitations:

- No eczema / dermatitis
- No skin-tone metadata
- Dermoscopic images only
- Multiple images per lesion, so split must be by `lesion_id` to avoid leakage

Suggested use:

- First baseline CNN dataset
- 3-class taxonomy: melanoma / benign nevus / other

## ISIC Challenge 2024 Training

Metadata summary:

- 401,059 rows/images
- 25 columns
- 1,042 unique patients
- 22,058 unique lesion IDs, but lesion ID missing in most rows
- All images are `TBP tile: close-up`

Diagnosis summary:

- Benign — 400,552
- Malignant — 393
- Indeterminate — 114

Detailed diagnosis is sparse:

- `diagnosis_2` missing in 399,991 rows
- Melanoma rows found: 157
- Inflammatory/infectious rows: 7, all verruca

Limitations:

- Extremely imbalanced
- Most labels are only broad benign/malignant
- No eczema/dermatitis
- No skin-tone metadata
- Different image type from HAM10000; possible domain shift

Suggested use:

- Do not use as primary MVP dataset
- Keep as possible supplemental/future benign-vs-malignant experiment

## ISIC Challenge 2019 Training

Metadata summary:

- 25,331 rows/images
- Dermoscopic images
- No skin-tone metadata

Useful classes:

- Nevus — 12,871
- Melanoma — 4,522
- Basal cell carcinoma — 3,323
- Seborrheic / pigmented keratosis — about 2,415 combined
- Actinic keratosis — 867
- Squamous cell carcinoma — 628
- Dermatofibroma — 239

Strengths:

- Larger than HAM10000
- Good for melanoma / nevus / other lesion classification
- Dermoscopic format consistent with HAM10000

Limitations:

- No eczema/dermatitis
- No skin-tone metadata
- Likely overlap with HAM10000 and other ISIC datasets, so deduplication is needed if combining

Suggested use:

- Possible alternative to HAM10000 as primary dermoscopic baseline
- Do not blindly merge with HAM10000

## ISIC-DICM-17K

Metadata summary:

- 17,060 rows/images
- Dermoscopic images
- Strong melanoma coverage
- Partial Fitzpatrick metadata, but mostly missing

Diagnosis highlights:

- Melanoma — 6,826
- Benign melanocytic proliferations — 3,516
- Basal cell carcinoma — 1,500
- Benign epidermal proliferations — 836
- Malignant epidermal proliferations — 678
- Inflammatory/infectious — 49

Skin-tone metadata:

- Fitzpatrick missing — 15,643
- I — 128
- II — 990
- III — 271
- IV — 28
- V–VI — 0

Strengths:

- Good melanoma-heavy supplemental dataset
- Partial skin-tone metadata can be discussed

Limitations:

- Not enough for full skin-tone fairness evaluation
- No Fitzpatrick V–VI in metadata
- Does not solve eczema/dermatitis

Suggested use:

- Optional melanoma-strengthening dataset
- Not primary fairness dataset

## MILK10k

Metadata summary:

- 10,480 rows/images
- 5,240 unique lesions
- Each lesion has 2 images
- 5,240 dermoscopic images
- 5,240 clinical close-up images

Diagnosis highlights:

- Malignant follicular/adnexal epithelial — 5,044
- Benign melanocytic proliferations — 1,492
- Melanoma — 900
- Benign epidermal proliferations — 1,090
- Squamous cell carcinoma / keratoacanthoma — 1,306
- Inflammatory or infectious diseases — 94

Strengths:

- Best product-aligned supplement inspected so far
- Contains both clinical close-up and dermoscopic images
- Manageable size
- Clean lesion pairing

Limitations:

- No skin-tone metadata in uploaded metadata file
- Inflammatory/infectious category is small
- Does not clearly support eczema/dermatitis
- Malignant-heavy distribution

Suggested use:

- Best supplement if team wants clinical-style images
- Possible primary dataset if product demo should look closer to real upload workflow
- Needs careful taxonomy mapping

---

# 9. Dataset Strategy Recommendation

## Short-term CNN baseline

Use one clean dataset first, not multiple merged datasets.

Recommended simplest baseline:

- HAM10000 with 3 classes: melanoma / benign nevus / other

Recommended product-aligned alternative:

- MILK10k with 3 classes: melanoma / benign nevus / other

## Do not merge blindly

Combining datasets may introduce:

- Duplicate images
- Overlap between HAM10000 and ISIC challenge data
- Domain shift between dermoscopic and clinical close-up images
- Different label taxonomies
- Different diagnosis confirmation standards
- Different patient/lesion ID availability

## Darker skin representation strategy

The team still needs datasets with darker skin types.

Priority candidates:

1. **DDI** — best fairness-audit dataset because it includes Fitzpatrick I–VI and darker skin representation.
2. **SCIN** — larger dataset with self-reported Fitzpatrick, estimated Fitzpatrick, and Monk Skin Tone metadata.
3. **Fitzpatrick17k** — possible supplement but needs quality inspection.

## Important distinction

Class labels are enough to train the first CNN classifier.

Skin-tone labels are not required for basic supervised training, but they are important for:

- fairness evaluation
- subgroup performance analysis
- responsible AI claims
- skin-tone-aware reliability warnings

Do not manually label thousands of images by skin tone for the MVP. It is subjective, slow, and unreliable.

---

# 10. Technical Architecture

## 3-week CNN MVP

```text
User uploads image
        ↓
Frontend upload + preview UI
        ↓
Backend / inference function
        ↓
Image preprocessing
        ↓
CNN classifier
        ↓
Top-3 class predictions + confidence scores
        ↓
Post-processing
        ↓
Uncertainty indicator + safety notes
        ↓
Frontend results UI
```

## Week 4 LLM extension

```text
CNN output
   ↓
Top-3 differential + confidence + uncertainty
   ↓
Structured prompt
   ↓
LLM explainer
   ↓
Validated JSON response
   ↓
Educational reasoning + learning Q&A
   ↓
Frontend explanation panel
```

LLM rule:

> The LLM explains the CNN output. It does not classify the image and does not provide diagnosis.

---

# 11. Success Metrics

## Primary product metric

> At least 70% of test users rate Revela 4/5 or 5/5 as useful for learning visual diagnostic reasoning.

## Secondary product metrics

- At least 80% prefer top-3 differential over a single prediction.
- At least 80% rate confidence/uncertainty as helpful.
- At least 70% rate visual-feature reasoning as helpful.
- At least 90% correctly identify Revela as educational, not diagnostic.
- At least 90% complete upload-to-result flow without help.

## Model metrics

- Top-3 accuracy: target around 70% for a credible prototype
- Macro-F1: report transparently; 0.60+ is a stretch target
- Balanced accuracy: report transparently
- Confusion matrix: required and interpreted
- Inference time: target under 10 seconds locally

## Safety metrics

- 100% of result screens show educational-only disclaimer.
- 0 unsafe diagnostic claims in UI.
- 100% of result screens include reliability/limitation note.
- Model/dataset transparency panel completed.

## Technical delivery metrics

- Local app runs successfully.
- Upload → CNN inference → result display works.
- Demo works three times in a row.
- README is complete enough for another person to run locally.

---

# 12. Key Concepts and Definitions

## Top-3 differential

Instead of one answer, the model returns three ranked possible classes with confidence scores.

Example:

- Melanoma — 76%
- Benign nevus — 16%
- Other / unclear — 8%

This supports clinical reasoning and avoids false certainty.

## Confidence score

The model’s probability-like score for each class. It is not medical certainty.

## Uncertainty indicator

A user-facing summary of how cautious the user should be.

Example thresholds:

- Low uncertainty: top-1 confidence ≥ 85%
- Medium uncertainty: top-1 confidence 60–84%
- High uncertainty: top-1 confidence < 60%

## Structured visual-feature reasoning

Short, scannable explanation of visible features that may support the result.

Example:

- Asymmetry
- Border irregularity
- Color variation
- Uneven pigmentation

For the MVP this can be static template text based on the top predicted class.

## Model/dataset transparency panel

An app or README section explaining:

- dataset used
- model type
- classes covered
- evaluation metrics
- known limitations
- clinical-use restrictions
- skin-tone metadata limitations

## Skin-tone slice evaluation

Evaluation of model performance by skin-tone group, e.g. Fitzpatrick I–II, III–IV, V–VI.

This requires reliable skin-tone metadata. If unavailable, do not claim fairness.

## Grad-CAM / heatmap

A model interpretability method that highlights image regions influencing prediction. Useful but not MVP-critical. Requires real CNN integration and careful interpretation.

---

# 13. Safety and Language Rules

## Avoid these phrases

- Diagnosis result
- You have melanoma
- Confirmed cancer
- The lesion is malignant
- This is benign
- The AI diagnosed
- Medical advice
- Treatment recommendation

## Use these phrases

- Differential suggestion
- May be consistent with
- Educational output
- Training aid only
- Not for diagnosis or patient care
- Model confidence is not clinical certainty
- Requires expert review in real clinical settings
- Reliability may vary by skin tone, image quality, lighting, and dataset coverage

## Persistent disclaimer

Use this in app and documentation:

> Educational training aid only. Not for diagnosis or patient care. Model output is for learning and case-review practice only.

## Reliability note

Use this in app and documentation:

> Model reliability may vary across skin tones, lighting, image quality, and dataset coverage. This result should be interpreted as an educational prompt, not clinical evidence.

---

# 14. Recommended 4-Week Plan

## Week 1 — Data + Baseline CNN

Goal:

- Select dataset
- Map labels
- Create split
- Build preprocessing
- Train baseline CNN

Deliverables:

- Dataset decision
- Metadata inspection report
- Label mapping table
- Train/validation/test split
- Baseline CNN model
- Initial metrics

## Week 2 — Model Improvement + Inference

Goal:

- Improve CNN
- Generate evaluation metrics
- Build inference function/API
- Return top-3 predictions

Deliverables:

- Final model artifact
- Top-3 prediction function
- Confidence scores
- Uncertainty logic
- Evaluation report
- Confusion matrix

## Week 3 — Frontend + End-to-End MVP

Goal:

- Create upload UI
- Connect to CNN inference
- Display results
- Add safety and transparency
- Prepare demo

Deliverables:

- Upload + preview UI
- Result panel
- Top-3 confidence bars
- Uncertainty label
- Static reasoning templates
- Model/dataset transparency panel
- README and demo script

## Week 4 — LLM Explanation Extension

Goal:

- Add controlled LLM explainer after CNN output

Deliverables:

- LLM prompt template
- Structured JSON schema
- LLM explain function/API
- Fallback to static templates
- LLM safety validation
- Generated learning Q&A

---

# 15. Team Workstreams

## ML/Data owner

Focus:

- Dataset inspection
- Label mapping
- Preprocessing
- CNN training
- Evaluation
- Model artifact

Important tasks:

- Do not merge datasets without checking overlap and label compatibility.
- Split by lesion ID where possible.
- Report macro-F1 and balanced accuracy, not only accuracy.
- Document limitations honestly.

## Backend/Integration owner

Focus:

- Model loading
- Inference function/API
- Top-3 post-processing
- Uncertainty logic
- JSON schema
- Week 4 LLM endpoint

Important tasks:

- Use same preprocessing in training and inference.
- Return consistent JSON.
- Handle invalid images gracefully.
- Never expose API keys in frontend.

## Frontend/Product owner

Focus:

- Upload UI
- Result display
- Confidence bars
- Reasoning templates
- Disclaimer and safety copy
- Transparency panel
- Demo script
- User testing survey

Important tasks:

- Keep UI clear and scannable.
- Avoid diagnostic wording.
- Make top-3 differential primary.
- Make uncertainty visible.
- Keep LLM explanation secondary to CNN output.

---

# 16. GitHub Project Structure

Recommended labels:

- P0 Must-have
- P1 Should-have
- P2 Could-have
- P3 Won’t-have
- Week 1
- Week 2
- Week 3
- Week 4
- Product
- Research
- Data
- ML
- Backend
- Frontend
- Integration
- Evaluation
- Safety
- LLM
- Documentation
- Demo
- QA
- Risk

Recommended columns:

- Backlog
- Ready
- In Progress
- Review / Testing
- Done
- Blocked

---

# 17. Minimum MVP Cutline

If the team runs out of time, protect only these:

- Dataset selected and documented
- 3-class taxonomy finalized
- Train/validation/test split created
- Preprocessing transform implemented
- CNN trained
- Model evaluation completed
- Top-3 prediction function implemented
- Confidence scores displayed
- Uncertainty indicator displayed
- Upload UI works
- Inference connected to UI
- Educational disclaimer shown
- Reliability limitation note shown
- README and demo script ready

Cut or defer:

- LLM
- Grad-CAM
- Skin-tone slice evaluation
- Quiz mode
- Deployment
- Educator flow
- Feedback analytics
- Fancy UI polish

---

# 18. Current Open Decisions

## Decision 1 — Dataset for first CNN baseline

Options:

1. HAM10000 — simplest known baseline
2. Challenge 2019 — larger dermoscopic baseline, possible overlap
3. MILK10k — best product-aligned because it includes clinical close-up images

Recommended decision:

- Use HAM10000 first if the team wants speed.
- Use MILK10k if the team wants better product fit.

## Decision 2 — Taxonomy

Recommended:

- Melanoma
- Benign nevus
- Other / unclear

Alternative:

- Melanoma
- Benign nevus
- Inflammatory / infectious
- Other / unclear

Only use the alternative if the team accepts the small inflammatory class and does not call it eczema.

## Decision 3 — Darker skin datasets

Priority:

1. DDI for fairness evaluation
2. SCIN for broader skin-tone metadata and common conditions
3. Fitzpatrick17k as optional supplement

## Decision 4 — Week 4 LLM

LLM should be added only after CNN + UI works.

The LLM should:

- Explain CNN output
- Generate learning Q&A
- Follow structured schema
- Fall back to templates
- Avoid diagnosis and treatment advice

---

# 19. Instructions for Other LLMs

When helping with this project, follow these rules:

1. Keep Revela framed as an educational dermatology training aid, not a diagnostic product.
2. Prioritize CNN classification first.
3. Treat LLM explanation as Week 4 extension.
4. Do not recommend free-form medical chatbot functionality.
5. Do not claim clinical safety or fairness without evidence.
6. Do not suggest manually labeling thousands of images by skin tone.
7. Prefer clear 3-class MVP taxonomy unless a reliable fourth class dataset is found.
8. Use top-3 differential, confidence, and uncertainty as core product requirements.
9. Always include limitations and non-diagnostic wording.
10. For dataset work, inspect metadata before downloading large image bundles.
11. For model evaluation, use top-3 accuracy, macro-F1, balanced accuracy, and confusion matrix.
12. For GitHub tickets, keep tasks atomic and testable in one day or less.

---

# 20. Short Summary for Quick Prompting

Revela is a CNN-first dermatology education MVP for residents. It lets a trainee upload a skin image and receive a top-3 differential with confidence scores, uncertainty, structured visual-feature reasoning, and safety/fairness limitations. The product is a clinical reasoning scaffold, not a diagnostic tool. The first 3-week MVP should train and present a CNN classifier; LLM explanation is a Week 4 extension only. Dataset inspection so far shows HAM10000, ISIC Challenge 2019, DICM-17K, and MILK10k support melanoma/nevus/other lesion classification but do not reliably support eczema/dermatitis. The realistic first taxonomy is melanoma / benign nevus / other unclear. The team still needs to inspect darker-skin datasets such as DDI and SCIN for fairness evaluation. The core success metric is whether at least 70% of test users rate Revela useful for learning visual diagnostic reasoning.

---

# 21. Current Model & Pipeline Status (updated 2026-05-19)

## Production taxonomy (replaces "3-class MVP" framing in earlier sections)

Following #116 / #117 (D3.1–D3.2), the dermoscopic CNN now uses a **4-class cancer-risk taxonomy** — not the older melanoma/nevus/other framing:

1. Melanoma
2. Non-melanoma skin cancer (BCC + SCC)
3. Benign nevus
4. Other non-cancer / indeterminate lesion (incl. actinic keratosis)

Reason: the old `Other lesion` class was hiding 4,235 NMSC cases (BCC + SCC) alongside benign lesions, making it impossible to communicate cancer risk. See DEC-008 in `docs/decision_log.md`.

## Trained dermoscopic CNN models on disk

| Model | Train data | Val macro-F1 | **Test melanoma recall** | **Test FNR** | Test macro-F1 | Checkpoint |
|---|---|---:|---:|---:|---:|---|
| BCN-only baseline (#119/#120) | BCN20000 train 12,352 | 0.6924 | 57.87% | 42.13% | 0.6581 | `models/bcn20000_cancer_risk_effnet_b0/best_model.pth` |
| **BCN+MNH (#141/#142)** | merged 21,233 (BCN train + filtered MNH) | 0.6768 | **61.36% (+3.50pp)** | **38.64% (−3.50pp)** | 0.6552 | `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` |

Both use EfficientNet-B0 / ImageNet pretrained / 224×224 / batch 16 / AdamW 3e-4 / 10 epochs / inverse-frequency class weights / best epoch by val_macro_f1. Test metrics evaluated on the identical frozen BCN20000 test set (md5 `a67861586e00812aadf46f2bdb4bc01b`, 2,659 rows).

## MNH (Mel+Nevus Histo) augmentation track — D4.1–D4.7

Histopathology-confirmed melanoma+nevus dataset from ISIC Archive (collection 294). Used to boost melanoma representation in the training pool while keeping the BCN20000 frozen test set untouched. Pipeline closed for D4.1–D4.5; D4.6 (evaluation on frozen test) and D4.7 (docs) remain.

| Stage | Issue | Output | Key numbers |
|---|---|---|---|
| Download | #137 ✅ | `data/mel_nevus_histo/{metadata,images/}` | 18,133 images, 7,191 melanoma |
| Filter BCN overlaps | #138 ✅ | `data/mel_nevus_histo/mnh_filtered.csv` | −5,633 dups → 12,500 rows |
| Map to taxonomy | #139 ✅ | `data/mel_nevus_histo/mnh_mapped.csv` + DEC-009 | Mel 4,345 · Nevus 8,050 · Other 105 · NMSC 0 |
| Merge + split | #140 ✅ | `splits/bcn_mnh_{train,val}.csv` | Train 21,233 · Val 3,619 |
| Retrain | #141 ✅ | `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` | Val macro-F1 0.6768 (BCN-only baseline 0.6924) |
| Evaluate | #142 ✅ | `outputs/metrics/bcn_mnh_*` | Test melanoma recall 61.4% (BCN-only 57.9%, +3.5pp); FNR 38.6% (−3.5pp); 20 fewer missed melanomas |
| Update docs | #143 ⏳ | `docs/{decision_log,llm_project_context}.md` | Next |

## Effect of MNH augmentation on training distribution

| Class | BCN-only train | BCN+MNH train | Δ |
|---|---:|---:|---:|
| Melanoma | 3,363 (27%) | 6,636 (31%) | **+97% rows** |
| Non-melanoma skin cancer | 2,968 (24%) | 2,537 (12%) | proportional drop (MNH adds none) |
| Benign nevus | 3,934 (32%) | 10,154 (48%) | +158% rows |
| Other / indeterminate | 2,087 (17%) | 1,906 (9%) | proportional drop |

## Decisions logged in `docs/decision_log.md`

- DEC-001 educational positioning
- DEC-002 BCN20000 for CNN v1
- DEC-008 dermoscopic CNN target = cancer-risk classification (4-class)
- DEC-009 MNH taxonomy mapping (collision lesions, indeterminate melanocytic, non-nevus pigmentations)

## Safety guarantees (asserted in code, not just documented)

- BCN20000 frozen test set (2,659 rows, md5 `a67861586e00812aadf46f2bdb4bc01b`) is **never** touched by training. Verified hash-stable across every D4.x notebook.
- Train/val/test isic_id intersections all asserted to be empty.
- Lesion-level no-leakage between train and val (`random.Random(seed=42).shuffle` of unique lesion_ids, then 70/15/15 slice — same logic as notebook 05).

## Notebooks (chronological)

| # | Purpose | Status |
|---|---|---|
| 05 | BCN20000 cancer-risk splits | done |
| 06 | Train BCN-only cancer-risk CNN | done |
| 07 | Evaluate BCN-only CNN (#120) | done |
| 08 | Download MNH (D4.1) | done |
| 09 | Filter BCN overlaps from MNH (D4.2) | done |
| 10 | Map MNH to cancer-risk taxonomy (D4.3) | done |
| 11 | Merge + lesion-grouped split (D4.4) | done |
| 12 | Train BCN+MNH CNN (D4.5) | done — guarded against accidental re-runs |
| 13 | Evaluate BCN+MNH on frozen BCN test (D4.6) | done — standalone PyTorch eval |

## What the team should know

- The 4-class cancer-risk taxonomy is the current production target, not the older 3-class framing.
- We now have two trained dermoscopic models. Both are EfficientNet-B0, same hyperparameters — only the training data differs. **The BCN+MNH model is the one to use going forward** — D4.6 (#142) confirmed +3.5 pp melanoma recall on the frozen test set.
- D4.6 verdict (head-to-head on the same 2,659-image test set):
  - Melanoma recall 57.9% → **61.4%** (+3.5 pp; 20 fewer missed melanomas)
  - Cancer (Mel+NMSC) recall 71.9% → 73.7% (+1.8 pp)
  - NMSC recall 72.4% → 75.3% (+2.9 pp — went up despite class share dropping in training)
  - Macro-F1: 0.6581 → 0.6552 (flat)
  - Trade-off direction is correct: both malignant classes gained recall, both benign classes gave a little back.
- The frozen BCN test set is sacred. Any new training data must hash-assert it before merging.
- Notebook 12 is hardened against accidental re-execution: training cells skip themselves if `training_history.csv` already has ≥10 epochs. This is a guardrail; if you want a true retrain, delete that file first.
