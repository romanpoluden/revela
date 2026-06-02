# Final Demo Image Set

This document defines a controlled image set for the final Revela demo and follow-up smoke testing.

## Scope and safety framing

- The selected images are for presentation, QA, and educational prototype demonstration only.
- The listed model outputs are recorded prototype outputs, not medical conclusions.
- Revela must not be presented as diagnosis, treatment advice, triage, referral guidance, biopsy guidance, clinical decision support, or patient-care direction.
- The stable demo paths point to copied benchmark files under `outputs/research/manual_llm_benchmark_images/` so the demo does not depend on unavailable original local dataset paths.

## Source files used

- `outputs/research/manual_llm_benchmark_images_index.csv`
- `outputs/research/manual_llm_image_benchmark_results_working.csv`
- `outputs/research/manual_llm_benchmark_images/`

## Selected cases

### demo_01 — Eczema / dermatitis

- **Stable demo path:** `outputs/research/manual_llm_benchmark_images/clinical_01_-1056928533969389753_image_1.jpg`
- **File exists locally:** yes
- **Source dataset:** google_scin
- **Image modality:** clinical/macroscopic
- **Intended demo flow:** clinical-photo review
- **Expected model ID:** `clinical_skin_condition_v1`
- **Ground truth / curated label:** Eczema / dermatitis
- **Recorded Revela top output:** Eczema / dermatitis
- **Recorded Revela top-k:** Eczema / dermatitis | Urticaria / allergic reaction | Folliculitis / acne-like
- **Recorded confidence:** 44.73
- **Clinical-to-dermoscopic follow-up:** no
- **Licensing/source note:** Copied from internal curated benchmark image set; original source metadata recorded in outputs/research/manual_llm_benchmark_images_index.csv
- **Safety note:** Presentation/demo use only. Educational prototype output, not diagnosis, treatment advice, triage, referral guidance, biopsy guidance, or clinical decision support.
- **Original path:** `data/raw/scin/images/train_-1056928533969389753_image_1.jpg`
- **Metadata notes:** split=test; case_id=-1056928533969389753; raw_label=Stasis Dermatitis

### demo_02 — Lesion — dermoscopic review recommended

- **Stable demo path:** `outputs/research/manual_llm_benchmark_images/clinical_09_2479491174478710673_image_1.jpg`
- **File exists locally:** yes
- **Source dataset:** google_scin
- **Image modality:** clinical/macroscopic
- **Intended demo flow:** clinical-photo review; demonstrates lesion-routing output and can be paired with a dermoscopic follow-up image for demo purposes
- **Expected model ID:** `clinical_skin_condition_v1`
- **Ground truth / curated label:** Lesion — dermoscopic review recommended
- **Recorded Revela top output:** Lesion — dermoscopic review recommended
- **Recorded Revela top-k:** Lesion — dermoscopic review recommended | Folliculitis / acne-like | Psoriasis / papulosquamous
- **Recorded confidence:** 83.36
- **Clinical-to-dermoscopic follow-up:** yes, demo workflow pairing only; not a confirmed same-patient pair
- **Licensing/source note:** Copied from internal curated benchmark image set; original source metadata recorded in outputs/research/manual_llm_benchmark_images_index.csv
- **Safety note:** Presentation/demo use only. Educational prototype output, not diagnosis, treatment advice, triage, referral guidance, biopsy guidance, or clinical decision support.
- **Original path:** `data/raw/scin/images/train_2479491174478710673_image_1.jpg`
- **Metadata notes:** split=test; case_id=2479491174478710673; raw_label=Actinic Keratosis
- **Correction note:** Recorded top output and top-k order corrected to match reviewer-confirmed current demo behavior. This remains educational/demo-only framing and is not a clinical claim.

### demo_03 — Melanoma

- **Stable demo path:** `outputs/research/manual_llm_benchmark_images/dermoscopic_01_ISIC_0057936.jpg`
- **File exists locally:** yes
- **Source dataset:** bcn20000
- **Image modality:** dermoscopic/magnified
- **Intended demo flow:** dermoscopic-image review
- **Expected model ID:** `dermoscopic_cancer_risk_bcn_mnh_v1`
- **Ground truth / curated label:** Melanoma
- **Recorded Revela top output:** Melanoma
- **Recorded Revela top-k:** Melanoma | Other non-cancer / indeterminate lesion | Benign nevus | Non-melanoma skin cancer
- **Recorded confidence:** 75.41
- **Clinical-to-dermoscopic follow-up:** n/a
- **Licensing/source note:** Copied from internal curated benchmark image set; original source metadata recorded in outputs/research/manual_llm_benchmark_images_index.csv
- **Safety note:** Presentation/demo use only. Educational prototype output, not diagnosis, treatment advice, triage, referral guidance, biopsy guidance, or clinical decision support.
- **Original path:** `data/raw/bcn20000/images/ISIC_0057936.jpg`
- **Metadata notes:** split=test; lesion_id=IL_0074934; diagnosis_3=Melanoma, NOS

### demo_04 — Non-melanoma skin cancer

- **Stable demo path:** `outputs/research/manual_llm_benchmark_images/dermoscopic_05_ISIC_0069513.jpg`
- **File exists locally:** yes
- **Source dataset:** bcn20000
- **Image modality:** dermoscopic/magnified
- **Intended demo flow:** dermoscopic-image review
- **Expected model ID:** `dermoscopic_cancer_risk_bcn_mnh_v1`
- **Ground truth / curated label:** Non-melanoma skin cancer
- **Recorded Revela top output:** Non-melanoma skin cancer
- **Recorded Revela top-k:** Non-melanoma skin cancer | Other non-cancer / indeterminate lesion | Melanoma | Benign nevus
- **Recorded confidence:** 87.82
- **Clinical-to-dermoscopic follow-up:** n/a
- **Licensing/source note:** Copied from internal curated benchmark image set; original source metadata recorded in outputs/research/manual_llm_benchmark_images_index.csv
- **Safety note:** Presentation/demo use only. Educational prototype output, not diagnosis, treatment advice, triage, referral guidance, biopsy guidance, or clinical decision support.
- **Original path:** `data/raw/bcn20000/images/ISIC_0069513.jpg`
- **Metadata notes:** split=test; lesion_id=IL_0106791; diagnosis_3=Basal cell carcinoma

### demo_05 — Other non-cancer / indeterminate lesion

- **Stable demo path:** `outputs/research/manual_llm_benchmark_images/dermoscopic_09_ISIC_0061167.jpg`
- **File exists locally:** yes
- **Source dataset:** bcn20000
- **Image modality:** dermoscopic/magnified
- **Intended demo flow:** dermoscopic-image review
- **Expected model ID:** `dermoscopic_cancer_risk_bcn_mnh_v1`
- **Ground truth / curated label:** Other non-cancer / indeterminate lesion
- **Recorded Revela top output:** Other non-cancer / indeterminate lesion
- **Recorded Revela top-k:** Other non-cancer / indeterminate lesion | Non-melanoma skin cancer | Melanoma | Benign nevus
- **Recorded confidence:** 95.6
- **Clinical-to-dermoscopic follow-up:** n/a
- **Licensing/source note:** Copied from internal curated benchmark image set; original source metadata recorded in outputs/research/manual_llm_benchmark_images_index.csv
- **Safety note:** Presentation/demo use only. Educational prototype output, not diagnosis, treatment advice, triage, referral guidance, biopsy guidance, or clinical decision support.
- **Original path:** `data/raw/bcn20000/images/ISIC_0061167.jpg`
- **Metadata notes:** split=test; lesion_id=IL_0142163; diagnosis_3=Seborrheic keratosis

## Deferred coverage

No benign-nevus case is included in the primary final demo set because the available stable benchmark candidates do not currently show matching intended top-output behavior. Benign-nevus mismatch cases can remain useful for limitations/failure analysis, but not for the primary presentation path.

## Acceptance criteria check

- Primary demo cases selected: 5.
- At least one clinical case: yes.
- At least one dermoscopic case: yes.
- All primary selected cases have top output matching intended presentation behavior: yes.
- Benign nevus primary presentation coverage: deferred because no available stable matching candidate is currently recorded.
- Clinical-to-dermoscopic follow-up case included or limitation documented: included as a demo-pair flow using a clinical lesion-routing case plus selected dermoscopic follow-up image; note that the images are not a true same-patient pair.
- Expected model outputs recorded: yes, from `outputs/research/manual_llm_image_benchmark_results_working.csv`.
- Demo image paths stable and usable locally: yes, copied benchmark image paths are used.
- Images not mislabeled as clinical vs dermoscopic: modalities are documented per curated benchmark metadata.
- No patient-identifying information included: no identifiers beyond dataset/image IDs are documented.
- No diagnosis or clinical-readiness claims made: yes; safety framing is included throughout.

## Known limitation

The clinical-to-dermoscopic follow-up case is a demo workflow pairing, not a confirmed same-patient clinical/dermoscopic image pair. It should be presented only as a workflow demonstration.

Machine-readable index: `outputs/demo/final_demo_image_set.csv`
