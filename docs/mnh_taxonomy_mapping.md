# MNH → Cancer-Risk Taxonomy Mapping

**Issue:** #139 (D4.3)
**Source:** `data/mel_nevus_histo/mnh_filtered.csv` (12,500 rows, post-BCN20000 dedup)
**Output:** `data/mel_nevus_histo/mnh_mapped.csv` — adds `cancer_risk_class` column.

The MNH dataset must map to the same four cancer-risk classes used in BCN20000 (DEC-008):
**Melanoma**, **Non-melanoma skin cancer**, **Benign nevus**, **Other non-cancer / indeterminate**.

MNH is entirely melanocytic / melanoma-focused — it contains **zero** non-melanoma skin cancers (BCC, SCC, actinic keratosis).

---

## 1. Full mapping table

| diagnosis_3 (or diagnosis_2 for NaN) | Rows | cancer_risk_class |
|---|---:|---|
| Nevus | 8,050 | Benign nevus |
| Melanoma, NOS | 2,502 | Melanoma |
| Melanoma in situ | 1,035 | Melanoma |
| Melanoma Invasive | 797 | Melanoma |
| Atypical melanocytic neoplasm | 70 | Other non-cancer / indeterminate |
| Collision - Only benign proliferations *(diagnosis_3 NaN)* | 15 | Other non-cancer / indeterminate |
| Collision - At least one malignant proliferation *(diagnosis_3 NaN)* | 11 | Melanoma |
| Epidermal nevus | 6 | Other non-cancer / indeterminate |
| Atypical intraepithelial melanocytic proliferation | 6 | Other non-cancer / indeterminate |
| Atypical proliferative nodules in congenital melanocytic nevus | 4 | Other non-cancer / indeterminate |
| Lentigo NOS | 3 | Other non-cancer / indeterminate |
| Mucosal melanotic macule | 1 | Other non-cancer / indeterminate |
| **Total** | **12,500** | |

---

## 2. Ambiguous-label decisions

### 2.1 Indeterminate melanocytic lesions (80 rows) → `Other non-cancer / indeterminate`

Affected labels: **Atypical melanocytic neoplasm** (70), **Atypical intraepithelial melanocytic proliferation** (6), **Atypical proliferative nodules in congenital melanocytic nevus** (4).

All carry `diagnosis_2 = "Indeterminate melanocytic proliferations"` — pathologists could not definitively classify as benign or malignant.

**Rationale:** Honest representation of label uncertainty. Mapping as `Melanoma` would inflate the cancer class with non-confirmed cases and pollute training signal. Mapping as `Benign nevus` would misrepresent risk. The 4th class explicitly includes "indeterminate" lesions for exactly this reason (DEC-008).

### 2.2 Non-melanocytic / non-nevus benign pigmentations (10 rows) → `Other non-cancer / indeterminate`

Affected labels: **Epidermal nevus** (6), **Lentigo NOS** (3), **Mucosal melanotic macule** (1).

None of these are true melanocytic nevi:
- *Epidermal nevus* — benign epidermal proliferation, not melanocytic (despite the name).
- *Lentigo NOS* — flat melanotic pigmentation, not a nevus.
- *Mucosal melanotic macule* — flat mucosal pigmentation, not a nevus.

**Rationale:** Mapping these as `Benign nevus` would dilute the BCN20000 nevus class with semantically different lesion types. `Other non-cancer / indeterminate` is the accurate destination.

### 2.3 Collision lesions (26 rows, diagnosis_3 NaN) → split by diagnosis_2

- **Collision - Only benign proliferations** (15) → `Other non-cancer / indeterminate`
- **Collision - At least one malignant proliferation** (11) → `Melanoma`

**Rationale:** Conservative on the malignant side — collision lesions containing melanoma must surface in melanoma recall. Benign-only collisions don't fit the single-lesion `Benign nevus` class cleanly, so they go to the indeterminate class.

---

## 3. Labels considered but not present in filtered MNH

The following labels appear in standard ISIC taxonomies but are absent from filtered MNH; no mapping needed:

- Basal cell carcinoma, Squamous cell carcinoma, Actinic keratosis (NMSC family)
- Spitz nevus, Blue nevus, Combined nevus, Reed nevus, Nevus NOS, Atypical/Dysplastic nevus
- Seborrheic keratosis, Dermatofibroma, Vascular lesion
- Melanoma metastasis

If a future MNH refresh introduces any of these, update this table and `TAXONOMY_MAP` in `Rehma_Revela/Notebook/10_map_mnh_taxonomy.ipynb`.

---

## 4. Final class distribution (mnh_mapped.csv)

| Class | Rows | % of MNH |
|---|---:|---:|
| Benign nevus | 8,050 | 64.4% |
| Melanoma | 4,345 | 34.8% |
| Non-melanoma skin cancer | 0 | 0.0% |
| Other non-cancer / indeterminate | 105 | 0.8% |
| **Total** | **12,500** | **100%** |

Melanoma count check: 4,334 (from `diagnosis_3` Melanoma/Invasive/in situ/NOS) + 11 (malignant collisions) = **4,345** ✅

Zero NaN in `cancer_risk_class` (asserted at runtime).

---

## 5. Implications for merge (D4.4)

MNH contributes only to two of the four classes meaningfully (Melanoma, Benign nevus). The NMSC class will remain entirely BCN20000-sourced. The merge will increase melanoma representation in the training set without affecting NMSC class balance.
