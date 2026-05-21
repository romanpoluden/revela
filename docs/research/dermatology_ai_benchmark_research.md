# Dermatology AI Benchmark Research

Issue: #166

This document positions Revela against existing dermatology AI benchmarks. It is benchmark positioning, not clinical validation. Revela remains an educational prototype. Model confidence is not clinical certainty, and no diagnosis or treatment claims are made.

## Executive Summary

Revela should not be presented as directly outperforming dermatology AI systems because the available external benchmarks use different datasets, image domains, taxonomies, and evaluation protocols. The strongest comparison is partial: DermaCon-IN is a recent clinical/macroscopic dermatology benchmark with reported accuracy, F1, and balanced accuracy for several architectures. SAMCL/PUMCH-ISD is adjacent because it is multimodal and inflammatory-disease focused. HierAttn, ISIC/HAM10000, PAD-UFES-20, and the current Revela dermoscopic branch are relevant to lesion-image benchmarking, but they do not share the same dataset or taxonomy as Revela Clinical V2.

Current Revela Clinical V2 baseline metrics:

- Accuracy: `0.6554` / `65.54%`
- Macro-F1: `0.6420` / `64.20%`
- Balanced accuracy: `0.6571` / `65.71%`
- SCIN macro-F1: `0.4028`
- Fitzpatrick17k macro-F1: `0.6366`
- Lesion-routing false negatives: `76`

Current Revela dermoscopic model:

- Model ID: `dermoscopic_cancer_risk_bcn_mnh_v1`
- Architecture: `efficientnet_b0`
- Taxonomy:
  1. `Melanoma`
  2. `Non-melanoma skin cancer`
  3. `Benign nevus`
  4. `Other non-cancer / indeterminate lesion`
- Exact evaluation metrics: not yet consolidated in benchmark doc.

## Comparability Framing

| Comparison type | Meaning for Revela |
|---|---|
| Direct | Same dataset, same split, same taxonomy, same metric definitions. None of the external benchmarks below are direct comparisons to Revela. |
| Partial | Similar image domain or task family, but dataset/taxonomy/evaluation differs. Useful for positioning only. |
| Adjacent | Similar research area, but modality, task, or model setup differs enough that metric comparison should be avoided. |
| Context only | Dataset landscape information, not a model performance benchmark. |

## Clinical / Macroscopic Benchmarks

### DermaCon-IN

DermaCon-IN is the most relevant external clinical/macroscopic benchmark in this shortlist because it reports multiple model architectures on an 8-main-class dermatology classification task. It is still only partially comparable to Revela because the dataset, geography, taxonomy, and class definitions differ.

| Model | Accuracy | F1 | Balanced accuracy | Comparability |
|---|---:|---:|---:|---|
| DermaCon-IN Swin-B/4W12-384 | 70.41 ± 0.41 | 69.69 ± 0.46 | 45.06 ± 0.02 | Partial |
| DermaCon-IN ViT-B/16-384 | 66.95 ± 0.19 | 65.78 ± 0.06 | 35.78 ± 0.02 | Partial |
| DermaCon-IN EffNet-B4 | 64.28 ± 0.34 | 63.38 ± 0.39 | 35.58 ± 0.01 | Partial |
| Revela Clinical V2 baseline | 65.54 | 64.20 macro-F1 | 65.71 | Internal reference only |

Why it matters:

- It gives a modern clinical-photo benchmark range for accuracy and F1.
- It shows that aggregate accuracy alone can hide poor balanced accuracy.
- It is useful for a presentation caveat: Revela’s Clinical V2 aggregate metrics sit in a plausible educational-prototype range, but this is not a direct benchmark comparison.

Main limitation:

- DermaCon-IN and Revela are not evaluated on the same data or taxonomy.

### SCIN Dataset Context

SCIN is relevant because Revela Clinical V2 reports source-specific performance on a SCIN-derived subset. SCIN is a clinical/macroscopic consumer-image dataset context, not by itself an external model benchmark in this document.

Why it matters:

- Revela’s SCIN macro-F1 is `0.4028`, much lower than its Fitzpatrick17k macro-F1.
- The source gap supports reporting source-specific metrics rather than only combined accuracy.

Main limitation:

- Same-source relevance means SCIN should be framed as dataset context, not independent external validation.

### Fitzpatrick17k Dataset Context

Fitzpatrick17k is relevant as a dermatology atlas and fairness context. Revela Clinical V2 reports Fitzpatrick17k macro-F1 `0.6366` on its source subset.

Why it matters:

- It motivates fairness/source reporting.
- It helps explain why source-specific results can differ sharply from combined results.

Main limitation:

- It is dataset context, not a standalone benchmark result for Revela.

## Dermoscopic And Lesion-Image Benchmarks

### HierAttn

HierAttn reports high accuracy on lesion-image datasets:

- ISIC2019 accuracy: `96.70%`
- PAD2020 accuracy: `91.22%`
- F1: not reported in accessible summary
- Code: `https://github.com/anthonyweidai/HierAttn`

Why it matters:

- It is a useful lesion-image benchmark reference for dermoscopic and smartphone lesion workflows.
- It shows the high-performance range that can appear on curated lesion datasets.

Main limitation:

- HierAttn uses different datasets and task framing. It is not directly comparable to Revela Clinical V2 or the BCN+MNH dermoscopic branch.

### ISIC / HAM10000 Context

ISIC challenges and HAM10000 are classic dermoscopic benchmark contexts. They are useful for explaining the dermoscopic branch landscape, but not for direct comparison to Revela’s current model unless the same split/taxonomy/protocol is used.

Why it matters:

- These datasets are recognizable to technical audiences.
- They anchor the dermoscopic model branch in a familiar benchmark family.

Main limitation:

- Dataset and taxonomy differ from the BCN+MNH educational dermoscopic model.

### PAD-UFES-20 Context

PAD-UFES-20/PAD2020 is a smartphone/macroscopic lesion dataset context and appears in lesion benchmark work such as HierAttn.

Why it matters:

- It is adjacent to Revela’s lesion-routing concept.
- It helps separate smartphone lesion images from dermoscopic images and from broad clinical skin-condition photos.

Main limitation:

- It is not a direct benchmark for Revela’s clinical inflammatory classes or BCN+MNH dermoscopic taxonomy.

## Multimodal / Foundation-Style Benchmarks

### SAMCL / PUMCH-ISD

SAMCL/PUMCH-ISD is adjacent because it combines clinical and dermoscopic signals and focuses on 8 inflammatory skin diseases.

Reported accessible-preview metrics:

- Accuracy: `0.822`
- Binary accuracy: `0.911`
- Derm7pt accuracy: `0.807`
- F1: not reported in accessible preview
- Kaggle dataset: `https://www.kaggle.com/datasets/jcwang10000/pumch-isd`
- GitHub: `https://github.com/vemvet/SAMCL`

Why it matters:

- It shows the direction of multimodal dermatology modeling.
- It is useful as an adjacent benchmark for future multimodal Revela work.

Main limitation:

- It is not comparable to Revela’s current single-image clinical and dermoscopic adapters.

## Benchmark Table

The machine-readable table is saved at:

- `outputs/research/dermatology_model_benchmark_table.csv`

## Recommended Benchmark Shortlist

Use this shortlist in the final presentation:

1. DermaCon-IN as the closest clinical/macroscopic external benchmark.
2. SCIN and Fitzpatrick17k as source-specific dataset context for Revela Clinical V2.
3. ISIC/HAM10000 and HierAttn as dermoscopic/lesion benchmark landscape references.
4. SAMCL/PUMCH-ISD as adjacent multimodal/foundation-style context.
5. PAD-UFES-20 as smartphone lesion context, not as a direct comparison.

## Limitations And Risks

- External metric comparisons are not direct unless the same test set, taxonomy, and preprocessing are used.
- Accuracy can be misleading under class imbalance; macro-F1, balanced accuracy, source-specific metrics, and error patterns should be shown together.
- Dataset overlap or same-source use can weaken claims of independent validation.
- Dermatology image domain matters: clinical photos, dermoscopy, smartphone lesion images, and multimodal inputs are not interchangeable.
- Presentation language must avoid clinical validation, diagnosis, treatment, or patient-use claims.

## References

- DermaCon-IN / arXiv 2506.06099v2: `https://arxiv.org/abs/2506.06099`
- SAMCL / PUMCH-ISD / ScienceDirect S0022202X25004026: `https://www.sciencedirect.com/science/article/pii/S0022202X25004026`
- SAMCL GitHub: `https://github.com/vemvet/SAMCL`
- PUMCH-ISD Kaggle: `https://www.kaggle.com/datasets/jcwang10000/pumch-isd`
- HierAttn / arXiv 2205.04326: `https://arxiv.org/abs/2205.04326`
- HierAttn GitHub: `https://github.com/anthonyweidai/HierAttn`
- SCIN dataset context: `https://research.google/blog/scin-a-dataset-for-skin-condition-images/`
- Fitzpatrick17k dataset context: `https://github.com/mattgroh/fitzpatrick17k`
- PAD-UFES-20 dataset context: `https://data.mendeley.com/datasets/zr7vgbcyr2/1`
- ISIC archive/challenges: `https://www.isic-archive.com/`
- HAM10000 dataset paper: `https://www.nature.com/articles/sdata2018161`
