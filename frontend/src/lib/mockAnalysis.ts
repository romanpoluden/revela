import { AIAnalysisResult, ImageWorkflow, InferenceResult } from "../types";
import {
  buildLearnerContextFromAnswers,
  buildLlmTransferPrompt,
  getCaseTypeFromInputType,
} from "./promptBuilder";

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
    structuredPrompt: "",
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
    structuredPrompt: "",
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

  const mockInferenceResult = buildMockInferenceResult(workflow, result);

  result.structuredPrompt = buildLlmTransferPrompt({
    caseType: getCaseTypeFromInputType(workflow.input_type),
    clinicalResponse: workflow.input_type === "clinical" ? mockInferenceResult : null,
    dermoscopicResponse: workflow.input_type === "dermoscopic" ? mockInferenceResult : null,
    learnerContext: buildLearnerContextFromAnswers(answers),
  });
  result.backendResult = mockInferenceResult;

  return result;
}

function buildMockInferenceResult(workflow: ImageWorkflow, analysis: AIAnalysisResult): InferenceResult {
  const predictions = analysis.topFindings.map((finding, index) => ({
    rank: index + 1,
    class_index: index,
    label: finding.label,
    probability: finding.probability / 100,
    confidence: finding.probability / 100,
    confidence_percent: finding.probability,
  }));

  return {
    model_id: workflow.model_id,
    model_name: "Frontend educational mock output",
    input_type: workflow.input_type,
    architecture: "frontend_mock",
    image_size: 0,
    predictions,
    top_prediction: predictions[0] ?? null,
    uncertainty: {
      bucket: analysis.confidenceScore >= 70 ? "higher_confidence" : "moderate_confidence",
      confidence: analysis.confidenceScore / 100,
      confidence_percent: analysis.confidenceScore,
      label: analysis.confidenceTier,
      explanation: "Frontend mock output for demo continuity. Model confidence is not clinical certainty.",
    },
    low_certainty: analysis.confidenceScore < 40,
    low_certainty_reason: analysis.confidenceScore < 40 ? "Mock confidence below demo low-certainty threshold." : null,
    low_certainty_message: analysis.confidenceScore < 40 ? "The model output is uncertain. Use for educational review only." : null,
    safety_note: analysis.safetyNote,
    model_limitations: [
      "This is frontend mock output for educational demonstration only.",
      "It is not clinical validation and must not be used for real-world decisions.",
      "Image quality, dataset coverage, and taxonomy scope limit interpretation.",
    ],
    recommended_next_step: "Use this output only for educational model-output review. Qualified review is required for real decisions.",
  };
}
