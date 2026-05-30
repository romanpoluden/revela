import { AIAnalysisResult } from "../types";

const STATIC_MOCK_ANALYSES: Record<string, AIAnalysisResult> = {
  "case-882-d": {
    topFindings: [
      {
        label: "Nodular Melanoma",
        probability: 94.2,
        description: "Example educational output noting asymmetric pigmentation, irregular borders, and varied visual structures for guided discussion.",
        category: "Malignant",
      },
      {
        label: "Pigmented Basal Cell Carcinoma",
        probability: 4.2,
        description: "Example alternative label included to support comparison of look-alike image patterns in a learning setting.",
        category: "Malignant",
      },
      {
        label: "Dysplastic Union Nevus",
        probability: 1.6,
        description: "Example learning label describing structural variability for comparison only.",
        category: "Premalignant",
      },
    ],
    confidenceScore: 94.2,
    confidenceTier: "High Model Confidence",
    timelineInsight: "Recent visible change is treated here as an educational discussion cue only. Real-world interpretation requires qualified review.",
    safetyNote: "Educational review only. This is not diagnosis or treatment advice, and qualified review is required for any real decision.",
    structuredPrompt: `[SYSTEM: EDUCATIONAL IMAGE REVIEW]
CASE ID: 882-D
SUBJECT: Educational review of an asymmetric pigmented lesion image.
FINDINGS:
- Morphology: 8mm nodular elevation, irregular borders.
- Pigmentation: Blue-white veil presence, atypical network.
- Vascularity: Polymorphic vessels, "milky-red" globules.
DIFFERENTIALS:
1. Nodular Melanoma (High Confidence)
2. Pigmented Basal Cell Carcinoma
REQUEST: Provide an educational comparison of these labels. Do not provide diagnosis, treatment advice, triage, or clinical validation.
`,
  },
  "case-8214": {
    topFindings: [
      {
        label: "Dysplastic Nevus",
        probability: 88.5,
        description: "Example educational output noting structural asymmetry and peripheral pigment variation for discussion.",
        category: "Premalignant",
      },
      {
        label: "Superficial Spreading Melanoma",
        probability: 9.8,
        description: "Example comparison label included to support model-output literacy.",
        category: "Malignant",
      },
      {
        label: "Severely Irritated Lentigo",
        probability: 1.7,
        description: "Example alternative label for comparing visually similar learning patterns.",
        category: "Benign",
      },
    ],
    confidenceScore: 88.5,
    confidenceTier: "Moderate Model Confidence",
    timelineInsight: "Timeline and history details are shown as educational context only and must not be used for real-world decisions without qualified review.",
    safetyNote: "Educational review only. This is not diagnosis or treatment advice, and qualified review is required for any real decision.",
    structuredPrompt: `[SYSTEM: EDUCATIONAL IMAGE REVIEW]
CASE ID: 8214
SUBJECT: Educational review of a dermatology learning image on dorsal hand.
FINDINGS:
- Margin: Ill-defined, showing early pigment dusting.
- Network: Bridging nests with peripheral progression.
- History: Strong family history of cutaneous melanoma.
DIFFERENTIAL DIAGNOSES:
1. Severely Atypical Dysplastic Nevus (Primary)
2. Early-stage Superficial Spreading Melanoma (Secondary)
REQUEST: Compare these labels for education only. Do not provide diagnosis, treatment advice, triage, or clinical validation.
`,
  },
  "case-304": {
    topFindings: [
      {
        label: "Seborrheic Keratosis",
        probability: 96.8,
        description: "Example educational output noting a stuck-on appearance and surface texture for discussion.",
        category: "Benign",
      },
      {
        label: "Pigmented Basal Cell Carcinoma",
        probability: 2.1,
        description: "Example alternative label included to support comparison of look-alike image patterns.",
        category: "Malignant",
      },
      {
        label: "Verrucous Melanoma",
        probability: 1.1,
        description: "Example comparison label for educational model-output literacy.",
        category: "Malignant",
      },
    ],
    confidenceScore: 96.8,
    confidenceTier: "High Model Confidence",
    timelineInsight: "A longer, unchanged timeline is presented as educational context only. Real-world interpretation requires qualified review.",
    safetyNote: "Educational review only. This is not diagnosis or treatment advice, and qualified review is required for any real decision.",
    structuredPrompt: `[SYSTEM: EDUCATIONAL IMAGE REVIEW]
CASE ID: 304-B
SUBJECT: Educational review of a textured lesion image.
FINDINGS:
- Texture: Verrucous, stuck-on waxy feel.
- Structures: Keratin plugs, comedo-like openings.
- Dynamic: Unchanged over multiple years, belt friction present.
DIFFERENTIALS:
1. Benign Seborrheic Keratosis (96.8% Confidence)
2. Pigmented Basal Cell Carcinoma (Rule Out mimicry)
REQUEST: Review image features for education only. Do not provide diagnosis, treatment advice, triage, or clinical validation.
`,
  },
};

export interface MockAnalysisInput {
  caseId: string;
  answers: Record<number, string>;
}

export async function runMockEducationalAnalysis({
  caseId,
  answers,
}: MockAnalysisInput): Promise<AIAnalysisResult> {
  await new Promise((resolve) => setTimeout(resolve, 1200));

  const selectedCase = STATIC_MOCK_ANALYSES[caseId] ?? STATIC_MOCK_ANALYSES["case-882-d"];
  const result = structuredClone(selectedCase);

  if (answers[5]?.toLowerCase().includes("no changes")) {
    result.topFindings[0].probability = Math.min(99.5, result.topFindings[0].probability + 2);
    result.confidenceScore = result.topFindings[0].probability;
  }

  return result;
}
