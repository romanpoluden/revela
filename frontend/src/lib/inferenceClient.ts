import {
  AIAnalysisResult,
  ImageWorkflow,
  InferenceBackendHealth,
  InferenceClientErrorCode,
  InferencePredictionItem,
  InferenceResult,
} from "../types";
import { runMockEducationalAnalysis } from "./mockAnalysis";
import {
  buildLearnerContextFromAnswers,
  buildLlmTransferPrompt,
  getCaseTypeFromInputType,
} from "./promptBuilder";

export interface AnalyzeCaseInput {
  workflow: ImageWorkflow;
  answers: Record<number, string>;
  customImage: string | null;
  imageFile: File | null;
  forceMock?: boolean;
}

export interface AnalyzeCaseResult {
  analysis: AIAnalysisResult;
  mode: "frontend-educational-mock" | "live-hf-inference";
}

export interface RunHfInferenceInput {
  image: Blob;
  modelId: string;
  topK: number;
}

export class InferenceClientError extends Error {
  code: InferenceClientErrorCode;
  status?: number;

  constructor(code: InferenceClientErrorCode, message: string, status?: number) {
    super(message);
    this.name = "InferenceClientError";
    this.code = code;
    this.status = status;
  }
}

const BACKEND_URL_ENV_KEY = "VITE_REVELA_INFERENCE_BACKEND_URL";
const LIVE_INFERENCE_ENV_KEY = "VITE_REVELA_ENABLE_LIVE_INFERENCE";

export async function checkInferenceBackendHealth(): Promise<InferenceBackendHealth> {
  const response = await requestInferenceBackend("/health", {
    method: "GET",
  });
  const payload: unknown = await response.json();

  if (!isInferenceBackendHealth(payload)) {
    throw new InferenceClientError(
      "invalid_response",
      "The inference backend health response was not in the expected format.",
    );
  }

  return payload;
}

export async function runHfInference({
  image,
  modelId,
  topK,
}: RunHfInferenceInput): Promise<InferenceResult> {
  const body = new FormData();
  body.append("model_id", modelId);
  body.append("top_k", String(topK));
  body.append("image", image);

  const response = await requestInferenceBackend("/predict", {
    method: "POST",
    body,
  });
  const payload: unknown = await response.json();

  if (!isInferenceResult(payload)) {
    throw new InferenceClientError(
      "invalid_response",
      "The inference backend output was not in the expected format.",
    );
  }

  return payload;
}

export async function analyzeCase(input: AnalyzeCaseInput): Promise<AnalyzeCaseResult> {
  if (!input.forceMock && shouldUseLiveInference() && hasInferenceBackendBaseUrl()) {
    if (!input.imageFile) {
      throw new InferenceClientError(
        "missing_image",
        "Upload an image before requesting live educational model output.",
      );
    }

    const backendResult = await runHfInference({
      image: input.imageFile,
      modelId: input.workflow.model_id,
      topK: input.workflow.top_k,
    });

    return {
      analysis: adaptInferenceResultToAnalysis(backendResult, input.workflow, input.answers),
      mode: "live-hf-inference",
    };
  }

  const analysis = await runMockEducationalAnalysis(input);

  return {
    analysis,
    mode: "frontend-educational-mock",
  };
}

function getInferenceBackendBaseUrl(): string {
  const rawUrl = readEnv(BACKEND_URL_ENV_KEY);

  if (!rawUrl) {
    throw new InferenceClientError(
      "missing_backend_url",
      "Inference backend URL is not configured. Set VITE_REVELA_INFERENCE_BACKEND_URL to enable future live inference.",
    );
  }

  return rawUrl.replace(/\/+$/, "");
}

function hasInferenceBackendBaseUrl(): boolean {
  return Boolean(readEnv(BACKEND_URL_ENV_KEY));
}

function shouldUseLiveInference(): boolean {
  return readEnv(LIVE_INFERENCE_ENV_KEY) === "true";
}

function readEnv(key: string): string | undefined {
  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
  return env?.[key]?.trim();
}

function adaptInferenceResultToAnalysis(
  result: InferenceResult,
  workflow: ImageWorkflow,
  answers: Record<number, string>,
): AIAnalysisResult {
  const topConfidence = result.top_prediction?.confidence ?? result.uncertainty.confidence ?? 0;
  const confidenceScore = toPercent(topConfidence, result.top_prediction?.confidence_percent);
  const structuredPrompt = buildLlmTransferPrompt({
    caseType: getCaseTypeFromInputType(workflow.input_type),
    clinicalResponse: workflow.input_type === "clinical" ? result : null,
    dermoscopicResponse: workflow.input_type === "dermoscopic" ? result : null,
    learnerContext: buildLearnerContextFromAnswers(answers),
  });

  return {
    topFindings: result.predictions.map((prediction) => {
      const probability = toPercent(prediction.confidence ?? prediction.probability ?? 0, prediction.confidence_percent);
      return {
        label: prediction.label,
        probability,
        description: `Educational model output from ${result.model_id}. Model confidence is not clinical certainty.`,
      };
    }),
    confidenceScore,
    confidenceTier: confidenceTierFromScore(confidenceScore),
    timelineInsight: result.low_certainty_message ?? result.uncertainty.explanation ?? "Model uncertainty metadata was returned by the inference backend.",
    safetyNote: [result.safety_note, ...result.model_limitations, result.recommended_next_step].filter(Boolean).join(" "),
    structuredPrompt,
    backendResult: result,
  };
}

function toPercent(confidence: number, confidencePercent?: number): number {
  if (typeof confidencePercent === "number") {
    return confidencePercent;
  }
  return Math.round(confidence * 10000) / 100;
}

function confidenceTierFromScore(score: number): AIAnalysisResult["confidenceTier"] {
  if (score >= 70) {
    return "High Model Confidence";
  }
  if (score >= 40) {
    return "Moderate Model Confidence";
  }
  return "Low Model Confidence";
}

async function requestInferenceBackend(path: string, init: RequestInit): Promise<Response> {
  const baseUrl = getInferenceBackendBaseUrl();

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, init);
  } catch {
    throw new InferenceClientError(
      "network_failure",
      "Could not reach the inference backend. Please check the backend URL and network connection.",
    );
  }

  if (!response.ok) {
    const detail = await readSafeErrorDetail(response);
    throw new InferenceClientError(
      "http_error",
      detail || `Inference backend returned HTTP ${response.status}.`,
      response.status,
    );
  }

  return response;
}

async function readSafeErrorDetail(response: Response): Promise<string | null> {
  try {
    const payload: unknown = await response.json();
    if (isRecord(payload)) {
      const detail = payload.detail ?? payload.message;
      if (typeof detail === "string") {
        return detail;
      }
    }
  } catch {
    return null;
  }

  return null;
}

function isInferenceBackendHealth(value: unknown): value is InferenceBackendHealth {
  return (
    isRecord(value) &&
    typeof value.status === "string" &&
    typeof value.version === "string" &&
    typeof value.device === "string" &&
    isStringArray(value.supported_model_ids) &&
    isStringArray(value.loaded_model_ids)
  );
}

function isInferenceResult(value: unknown): value is InferenceResult {
  return (
    isRecord(value) &&
    typeof value.model_id === "string" &&
    typeof value.input_type === "string" &&
    typeof value.architecture === "string" &&
    typeof value.image_size === "number" &&
    Array.isArray(value.predictions) &&
    value.predictions.every(isInferencePredictionItem) &&
    (value.top_prediction === null || isInferencePredictionItem(value.top_prediction)) &&
    isRecord(value.uncertainty) &&
    typeof value.low_certainty === "boolean" &&
    isNullableString(value.low_certainty_reason) &&
    isNullableString(value.low_certainty_message) &&
    typeof value.safety_note === "string" &&
    isStringArray(value.model_limitations) &&
    typeof value.recommended_next_step === "string"
  );
}

function isInferencePredictionItem(value: unknown): value is InferencePredictionItem {
  return (
    isRecord(value) &&
    typeof value.label === "string" &&
    (value.rank === undefined || typeof value.rank === "number") &&
    (value.class_index === undefined || typeof value.class_index === "number") &&
    (value.probability === undefined || typeof value.probability === "number") &&
    (value.confidence === undefined || typeof value.confidence === "number") &&
    (value.confidence_percent === undefined || typeof value.confidence_percent === "number")
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}
