import {
  AIAnalysisResult,
  ImageWorkflow,
  InferenceBackendHealth,
  InferenceClientErrorCode,
  InferencePredictionItem,
  InferenceResult,
} from "../types";
import { runMockEducationalAnalysis } from "./mockAnalysis";

export interface AnalyzeCaseInput {
  workflow: ImageWorkflow;
  answers: Record<number, string>;
  customImage: string | null;
}

export interface AnalyzeCaseResult {
  analysis: AIAnalysisResult;
  mode: "frontend-educational-mock";
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
  // Future production inference should call the Revela Hugging Face backend API client here.
  // Until that API client exists, keep demo behavior local and explicit.
  const analysis = await runMockEducationalAnalysis(input);

  return {
    analysis,
    mode: "frontend-educational-mock",
  };
}

function getInferenceBackendBaseUrl(): string {
  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
  const rawUrl = env?.[BACKEND_URL_ENV_KEY]?.trim();

  if (!rawUrl) {
    throw new InferenceClientError(
      "missing_backend_url",
      "Inference backend URL is not configured. Set VITE_REVELA_INFERENCE_BACKEND_URL to enable future live inference.",
    );
  }

  return rawUrl.replace(/\/+$/, "");
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
