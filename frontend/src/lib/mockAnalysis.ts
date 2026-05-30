import { AIAnalysisResult } from "../types";

const STATIC_MOCK_ANALYSES: Record<string, AIAnalysisResult> = {
  "case-882-d": {
    topFindings: [
      {
        diagnosis: "Nodular Melanoma",
        probability: 94.2,
        description: "Asymmetric pigmentation showing an active blue-white veil, irregular borders, and polymorphic atypical clinical vasculature. High concern for aggressive deep-tissue replication.",
        category: "Malignant",
      },
      {
        diagnosis: "Pigmented Basal Cell Carcinoma",
        probability: 4.2,
        description: "May present with shiny waxy nodules and hyperpigmented globules resembling a nest, though vascular patterns favor melanocytic tumor.",
        category: "Malignant",
      },
      {
        diagnosis: "Dysplastic Union Nevus",
        probability: 1.6,
        description: "Severely atypical nevus. Exhibits structural variability but generally lacks the profound architectural disruption seen in high-grade melanoma.",
        category: "Premalignant",
      },
    ],
    confidenceScore: 94.2,
    confidenceTier: "High Certainty",
    timelineInsight: "Rapid evolution within a 1-6 month timeframe in a 64-year-old male is highly correlation-indicative of clinical malignancy. Melanosomes demonstrate accelerated, uncontrolled epidermal-dermal penetration.",
    clinicalAction: "Immediate excisional biopsy with 1-2mm margins is recommended. Urgent referral to clinical neuro/dermatological oncology within 48 hours is vital.",
    structuredPrompt: `[SYSTEM: CLINICAL PATHOLOGY ANALYST]
CASE ID: 882-D
SUBJECT: Dermoscopic assessment of asymmetric pigmented lesion.
FINDINGS:
- Morphology: 8mm nodular elevation, irregular borders.
- Pigmentation: Blue-white veil presence, atypical network.
- Vascularity: Polymorphic vessels, "milky-red" globules.
DIFFERENTIALS:
1. Nodular Melanoma (High Confidence)
2. Pigmented Basal Cell Carcinoma
REQUEST: Provide a comparative analysis of these differentials focusing on atypical vascular patterns observed in high-resolution specimen imagery.
`,
  },
  "case-8214": {
    topFindings: [
      {
        diagnosis: "Dysplastic Nevus",
        probability: 88.5,
        description: "Significant structural asymmetry, bridging of nests, and minor irregular peripheral pigment streaks. Mild to moderate keratinocyte atypia.",
        category: "Premalignant",
      },
      {
        diagnosis: "Superficial Spreading Melanoma",
        probability: 9.8,
        description: "Early phase superficial spread. Features marginal regression but retains structured peripheral networks.",
        category: "Malignant",
      },
      {
        diagnosis: "Severely Irritated Lentigo",
        probability: 1.7,
        description: "Inflammatory infiltration mimicking early melanocytic proliferation, but dermoscopy reveals intact follicular preservation.",
        category: "Benign",
      },
    ],
    confidenceScore: 88.5,
    confidenceTier: "Moderate Certainty",
    timelineInsight: "Steady alteration over 1-4 weeks coupled with a positive family history of melanoma calls for careful diagnostic tracking. Marked architectural disarray is present.",
    clinicalAction: "Complete narrow excisional biopsy is prudent to rule out early superficial melanocytic proliferation. Routine dermoscopic mapping of active satellite lesions.",
    structuredPrompt: `[SYSTEM: PATHOLOGY EXPERT ASSIST]
CASE ID: 8214
SUBJECT: Dermoscopic evaluation of atypical melanocytic proliferation on dorsal hand.
FINDINGS:
- Margin: Ill-defined, showing early pigment dusting.
- Network: Bridging nests with peripheral progression.
- History: Strong family history of cutaneous melanoma.
DIFFERENTIAL DIAGNOSES:
1. Severely Atypical Dysplastic Nevus (Primary)
2. Early-stage Superficial Spreading Melanoma (Secondary)
REQUEST: Synthesize histopathological criteria distinguishing these two conditions in a 42-year-old patient.
`,
  },
  "case-304": {
    topFindings: [
      {
        diagnosis: "Seborrheic Keratosis",
        probability: 96.8,
        description: "Classic stuck-on hyperkeratotic plaque, with prominent fat-like keratin cysts, comedo-like openings, and fingerprint-like epidermal ridges.",
        category: "Benign",
      },
      {
        diagnosis: "Pigmented Basal Cell Carcinoma",
        probability: 2.1,
        description: "Could present with stuck-on appearance but lacks the typical keratin plugs and horn cysts characteristic of seborrheic entities.",
        category: "Malignant",
      },
      {
        diagnosis: "Verrucous Melanoma",
        probability: 1.1,
        description: "Rare architectural mimic showing verrucous surface, though vascular patterns remain regular and quiet.",
        category: "Malignant",
      },
    ],
    confidenceScore: 96.8,
    confidenceTier: "High Certainty",
    timelineInsight: "Long-standing, non-evolving lesion showing zero progression over several months is highly reassuring. Typical benign maturation of squamous cells is observed.",
    clinicalAction: "No immediate clinical treatment is required unless symptomatic (irritated by belt). Cryotherapy or light curettage can be performed for patient relief.",
    structuredPrompt: `[SYSTEM: CLINICAL EDUCATION LAB]
CASE ID: 304-B
SUBJECT: Stuck-on hyperkeratotic lesion of flank.
FINDINGS:
- Texture: Verrucous, stuck-on waxy feel.
- Structures: Keratin plugs, comedo-like openings.
- Dynamic: Unchanged over multiple years, belt friction present.
DIFFERENTIALS:
1. Benign Seborrheic Keratosis (96.8% Confidence)
2. Pigmented Basal Cell Carcinoma (Rule Out mimicry)
REQUEST: Review the benign diagnostic features under polarized dermoscopy.
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
