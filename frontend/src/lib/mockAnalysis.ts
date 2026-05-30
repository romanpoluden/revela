import { AIAnalysisResult, ImageWorkflow } from "../types";

const STATIC_MOCK_ANALYSES: Record<ImageWorkflow["input_type"], AIAnalysisResult> = {
  clinical: {
    topFindings: [
      {
        label: "Clinical image pattern",
        probability: 72.4,
        description: "Example educational model output for a regular camera photo workflow.",
        category: "Benign",
      },
      {
        label: "Visible surface-change pattern",
        probability: 18.7,
        description: "Example alternative label included to support image workflow review.",
        category: "Premalignant",
      },
      {
        label: "Color variation pattern",
        probability: 8.9,
        description: "Example comparison label for educational model-output literacy.",
        category: "Benign",
      },
    ],
    confidenceScore: 72.4,
    confidenceTier: "Moderate Model Confidence",
    timelineInsight: "Recent visible change is treated here as an educational discussion cue only. Real-world interpretation requires qualified review.",
    safetyNote: "Educational review only. This is not diagnosis or treatment advice, and qualified review is required for any real decision.",
    structuredPrompt: `[SYSTEM: EDUCATIONAL IMAGE REVIEW]
IMAGE WORKFLOW: clinical / macroscopic photo
MODEL ID: clinical_skin_condition_v1
TOP K: 3
REQUEST: Provide an educational comparison of these labels. Do not provide diagnosis, treatment advice, triage, or clinical validation.
`,
  },
  dermoscopic: {
    topFindings: [
      {
        label: "Dermoscopic lesion-pattern output",
        probability: 81.6,
        description: "Example educational model output for a dermoscopic or magnified lesion image workflow.",
        category: "Premalignant",
      },
      {
        label: "Pigment-network variation",
        probability: 12.9,
        description: "Example alternative label for comparing visually similar learning patterns.",
        category: "Benign",
      },
      {
        label: "Asymmetry cue pattern",
        probability: 5.5,
        description: "Example comparison label for educational model-output literacy.",
        category: "Malignant",
      },
      {
        label: "Border cue pattern",
        probability: 0,
        description: "Example comparison label for educational model-output literacy.",
        category: "Premalignant",
      },
    ],
    confidenceScore: 81.6,
    confidenceTier: "High Model Confidence",
    timelineInsight: "A longer, unchanged timeline is presented as educational context only. Real-world interpretation requires qualified review.",
    safetyNote: "Educational review only. This is not diagnosis or treatment advice, and qualified review is required for any real decision.",
    structuredPrompt: `[SYSTEM: EDUCATIONAL IMAGE REVIEW]
IMAGE WORKFLOW: dermoscopic / magnified lesion image
MODEL ID: dermoscopic_cancer_risk_bcn_mnh_v1
TOP K: 4
REQUEST: Review image features for education only. Do not provide diagnosis, treatment advice, triage, or clinical validation.
`,
  },
};

export interface MockAnalysisInput {
  workflow: ImageWorkflow;
  answers: Record<number, string>;
}

export async function runMockEducationalAnalysis({
  workflow,
  answers,
}: MockAnalysisInput): Promise<AIAnalysisResult> {
  await new Promise((resolve) => setTimeout(resolve, 1200));

  const selectedWorkflow = STATIC_MOCK_ANALYSES[workflow.input_type];
  const result = structuredClone(selectedWorkflow);

  if (answers[5]?.toLowerCase().includes("no changes")) {
    result.topFindings[0].probability = Math.min(99.5, result.topFindings[0].probability + 2);
    result.confidenceScore = result.topFindings[0].probability;
  }

  return result;
}
