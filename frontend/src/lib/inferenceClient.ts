import { AIAnalysisResult } from "../types";
import { runMockEducationalAnalysis } from "./mockAnalysis";

export interface AnalyzeCaseInput {
  caseId: string;
  answers: Record<number, string>;
  customImage: string | null;
}

export interface AnalyzeCaseResult {
  analysis: AIAnalysisResult;
  mode: "frontend-educational-mock";
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
