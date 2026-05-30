export interface ImageWorkflow {
  id: string;
  title: string;
  description: string;
  model_id: string;
  top_k: number;
  input_type: 'clinical' | 'dermoscopic';
}

export interface QuizQuestion {
  id: number;
  questionText: string;
  description?: string;
  options: string[];
}

export interface AIAnalysisResult {
  topFindings: {
    label: string;
    probability: number;
    description: string;
    category: 'Malignant' | 'Benign' | 'Premalignant';
  }[];
  confidenceScore: number;
  confidenceTier: 'High Model Confidence' | 'Moderate Model Confidence' | 'Low Model Confidence';
  timelineInsight: string;
  safetyNote: string;
  structuredPrompt: string;
}

export const IMAGE_WORKFLOWS: ImageWorkflow[] = [
  {
    id: "clinical",
    title: "Clinical / macroscopic photo",
    description: "Regular camera photo of a visible skin condition. Not dermoscopic, not microscope, not highly magnified.",
    model_id: "clinical_skin_condition_v1",
    top_k: 3,
    input_type: "clinical",
  },
  {
    id: "dermoscopic",
    title: "Dermoscopic / magnified lesion image",
    description: "Dermoscopic or magnified lesion image. Model output is educational only and not diagnosis.",
    model_id: "dermoscopic_cancer_risk_bcn_mnh_v1",
    top_k: 4,
    input_type: "dermoscopic",
  },
];

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    id: 1,
    questionText: "How long have you noticed this?",
    description: "Timing is included only as educational context for discussing image workflows.",
    options: ["A few days", "1–4 weeks", "1–6 months", "More than 6 months", "I'm not sure"]
  },
  {
    id: 2,
    questionText: "Where is the lesion located?",
    description: "Location is included only as educational context for comparing image examples.",
    options: ["Posterior thorax / Back", "Dorsal hand / Extremities", "Head / Neck", "Trunk / Abdomen", "Other skin fold"]
  },
  {
    id: 3,
    questionText: "Are there any associated physical symptoms?",
    description: "These options are learning-context signals only and are not used for real-world decisions.",
    options: ["Asymptomatic (No symptoms)", "Mild pruritus / Itching", "Bleeding, oozing, or ulceration", "Mild tenderness / Pain", "Rapid physical enlargement only"]
  },
  {
    id: 4,
    questionText: "Is there a personal or family history of skin cancer?",
    description: "Background context is included only for educational discussion.",
    options: ["Yes (Melanoma)", "Yes (Basal / Squamous Cell)", "Yes (Family history only)", "No history of skin cancer", "I am not sure"]
  },
  {
    id: 5,
    questionText: "Has it changed recently?",
    description: "Recent visible change is included only as educational context for model-output review.",
    options: ["No changes noticed", "It seems to be growing", "The color has changed", "It's spreading to other areas", "Several multi-attribute changes"]
  }
];
