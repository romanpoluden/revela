import { InferenceResult } from "../types";

const SAFETY_HEADER = `This is an educational dermatology training case for structured model output review.
This is NOT a diagnosis. Do not recommend treatment. Model confidence is not clinical certainty.
Qualified review is required for real decisions.`;

const LLM_INSTRUCTIONS_SINGLE = `=== Instructions for the AI assistant ===

Please treat this as an educational dermatology training case. Your task is to:

1. Explain the Revela model output in learning-friendly terms for a medical education context.
2. Compare the top model alternatives and explain what visual or contextual features might
   support or weaken each category from the supplied taxonomy.
3. Discuss the uncertainty level and what it means for educational interpretation.
4. Briefly explain the model's stated limitations.
5. Suggest 2–3 non-identifying follow-up questions a learner could explore to deepen understanding.
6. Stay within the supplied taxonomy classes — do not introduce diagnoses outside this list.

Important constraints:
- Do NOT diagnose the patient.
- Do NOT recommend treatment.
- Do NOT claim clinical certainty.
- Do NOT describe any output as "safe", "confirmed", or "detected".
- "Other non-cancer / indeterminate lesion" does NOT mean safe — explain this if it appears.
- Frame all discussion as educational model output review, not clinical conclusions.
- Qualified review by a licensed clinician is required for any real decision.`;

const LLM_INSTRUCTIONS_PAIRED = `=== Instructions for the AI assistant ===

Please treat this as a paired educational dermatology training case with both a clinical-photo
model output and a dermoscopic-image model output. Your task is to:

1. Explain each Revela model output in learning-friendly terms.
2. Discuss what visual or contextual features might support or weaken the top alternatives
   from each model's taxonomy.
3. Compare the two model outputs educationally — where they agree, where they differ,
   and why that matters for a learner.
4. Discuss uncertainty for each output and what it means for educational interpretation.
5. Briefly explain the models' limitations.
6. Suggest 2–3 non-identifying follow-up questions a learner could explore.
7. Stay within the supplied taxonomy classes for each model.

Important constraints:
- Do NOT diagnose the patient.
- Do NOT recommend treatment.
- Do NOT claim clinical certainty.
- Do NOT describe any output as "safe", "confirmed", or "detected".
- "Other non-cancer / indeterminate lesion" does NOT mean safe — explain this if it appears.
- Frame all discussion as educational model output review, not clinical conclusions.
- Qualified review by a licensed clinician is required for any real decision.`;

const LOW_CERTAINTY_BLOCK = `=== Low-Certainty Notice ===
One or more Revela outputs were marked low-certainty. Please prioritise:
- Discussion of uncertainty and what it means for educational review.
- Alternative possibilities from the model taxonomy.
- What additional context, image quality, or further review might help.
Do not make a firm conclusion from this output alone.`;

export interface BuildLlmTransferPromptInput {
  caseType: string;
  clinicalResponse?: InferenceResult | null;
  dermoscopicResponse?: InferenceResult | null;
  learnerContext?: Record<string, string> | null;
  learnerRating?: Record<string, string | number | boolean | null | undefined> | null;
}

export function buildLlmTransferPrompt({
  caseType,
  clinicalResponse,
  dermoscopicResponse,
  learnerContext,
  learnerRating,
}: BuildLlmTransferPromptInput): string {
  const isPaired = caseType === "Paired clinical + dermoscopic case";
  const hasClinical = Boolean(clinicalResponse);
  const hasDermoscopic = Boolean(dermoscopicResponse);

  if (!hasClinical && !hasDermoscopic) {
    return [
      "Prompt export is unavailable because model output is unavailable.",
      "Please re-run the analysis or upload a supported image.",
    ].join("\n");
  }

  const hasLowCertainty =
    (clinicalResponse ? isLowCertainty(clinicalResponse) : false) ||
    (dermoscopicResponse ? isLowCertainty(dermoscopicResponse) : false);

  const parts: string[] = [];

  parts.push("=== Revela Educational Case Prompt ===");
  parts.push("");
  parts.push(SAFETY_HEADER);
  parts.push("");
  parts.push("--- Case Type ---");
  parts.push(caseType);
  parts.push("");

  if (clinicalResponse) {
    parts.push("--- Clinical Model Output (clinical_skin_condition_v1) ---");
    parts.push("Input type: Clinical macroscopic photo");
    parts.push("");
    parts.push(...formatResponseBlock(clinicalResponse));
    parts.push("");
  }

  if (dermoscopicResponse) {
    parts.push("--- Dermoscopic Model Output (dermoscopic_cancer_risk_bcn_mnh_v1) ---");
    parts.push("Input type: Dermoscopic / close-up lesion image");
    parts.push("");
    parts.push(...formatResponseBlock(dermoscopicResponse));
    parts.push("");
  }

  const contextLines = formatLearnerContext(learnerContext);
  if (contextLines.length > 0) {
    parts.push("--- Learner Context (provided before analysis; not used as model input) ---");
    parts.push(...contextLines);
    parts.push("");
  }

  const ratingLines = formatLearnerRating(learnerRating);
  if (ratingLines.length > 0) {
    parts.push("--- Learner Reflection (not a diagnosis; does not change model output) ---");
    parts.push(...ratingLines);
    parts.push("");
  }

  if (hasLowCertainty) {
    parts.push(LOW_CERTAINTY_BLOCK);
    parts.push("");
  }

  parts.push(isPaired ? LLM_INSTRUCTIONS_PAIRED : LLM_INSTRUCTIONS_SINGLE);

  return parts.join("\n");
}

export function buildLearnerContextFromAnswers(answers: Record<number, string>): Record<string, string> {
  return {
    duration: answers[1] ?? "not provided",
    body_location: answers[2] ?? "not provided",
    symptoms: answers[3] ?? "not provided",
    skin_cancer_history: answers[4] ?? "not provided",
    change_over_time: answers[5] ?? "not provided",
  };
}

export function getCaseTypeFromInputType(inputType: string): string {
  if (inputType === "clinical") {
    return "Clinical macroscopic photo case";
  }

  if (inputType === "dermoscopic") {
    return "Dermoscopic image case";
  }

  return "Single image educational case";
}

function isLowCertainty(response: InferenceResult): boolean {
  return response.low_certainty === true || response.uncertainty?.bucket === "low_confidence";
}

function formatResponseBlock(response: InferenceResult): string[] {
  const lines: string[] = [];
  const top = response.top_prediction;
  const label = top?.label ?? "Unavailable";
  const confidence = formatConfidence(top?.confidence_percent, top?.confidence ?? top?.probability);

  lines.push(`Top output: ${label} (${confidence})`);

  const uncertaintyLabel = response.uncertainty?.label ?? "Unavailable";
  const uncertaintyExplanation = response.uncertainty?.explanation ?? "";
  lines.push(`Uncertainty: ${uncertaintyLabel}`);

  if (uncertaintyExplanation) {
    lines.push(`  ${uncertaintyExplanation}`);
  }

  if (response.low_certainty === true) {
    const lowCertaintyMessage = response.low_certainty_message ?? "The model output is uncertain. Use for educational review only.";
    lines.push(`Low-certainty flag: ${lowCertaintyMessage}`);

    if (response.low_certainty_reason) {
      lines.push(`  Reason: ${response.low_certainty_reason}`);
    }
  }

  if (response.predictions.length > 0) {
    lines.push("");
    lines.push("All model outputs:");
    response.predictions.forEach((prediction, index) => {
      const rank = prediction.rank ?? index + 1;
      const predictionConfidence = formatConfidence(
        prediction.confidence_percent,
        prediction.confidence ?? prediction.probability,
      );
      lines.push(`  ${rank}. ${prediction.label} — ${predictionConfidence}`);
    });
  }

  if (response.safety_note) {
    lines.push("");
    lines.push(`Safety note: ${response.safety_note}`);
  }

  if (response.model_limitations.length > 0) {
    lines.push("Model limitations:");
    response.model_limitations.forEach((limitation) => {
      lines.push(`  - ${limitation}`);
    });
  }

  if (response.recommended_next_step) {
    lines.push(`Recommended next step: ${response.recommended_next_step}`);
  }

  return lines;
}

function formatConfidence(confidencePercent?: number, confidence?: number): string {
  if (typeof confidencePercent === "number") {
    return `${confidencePercent.toFixed(2)}%`;
  }

  if (typeof confidence === "number") {
    return `${(confidence * 100).toFixed(2)}%`;
  }

  return "Unavailable";
}

function formatLearnerContext(context?: Record<string, string> | null): string[] {
  if (!context) {
    return [];
  }

  const labels: Record<string, string> = {
    body_location: "Body location",
    duration: "Duration",
    symptoms: "Symptoms",
    itching: "Itching",
    pain_tenderness: "Pain / tenderness",
    change_over_time: "Change over time",
    bleeding_crusting_discharge: "Bleeding / crusting / discharge",
    prior_episodes: "Prior similar episodes",
    image_quality_concern: "Image quality concern",
    skin_cancer_history: "Personal/family skin cancer history",
    learner_note: "Learner note",
  };

  return Object.entries(labels).flatMap(([key, label]) => {
    const value = context[key];
    if (!value || value === "not provided") {
      return [];
    }
    return [`${label}: ${value}`];
  });
}

function formatLearnerRating(rating?: Record<string, string | number | boolean | null | undefined> | null): string[] {
  if (!rating) {
    return [];
  }

  const lines: string[] = [];
  const concern = rating.concern;
  const prioritize = rating.prioritize_dermoscopy;
  const cues = typeof rating.visible_cues === "string" ? rating.visible_cues.trim() : "";

  if (typeof concern === "number") {
    lines.push(`Concern level: ${concern} / 5`);
  }

  if (prioritize) {
    lines.push(`Would prioritize dermoscopic review: ${prioritize}`);
  }

  if (cues) {
    lines.push(`Visible cues noted: ${cues}`);
  }

  return lines;
}
