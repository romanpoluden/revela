export interface CaseImage {
  id: string;
  url: string;
  alt: string;
  type: 'clinical' | 'dermoscopic';
}

export interface PresetCase {
  id: string;
  name: string;
  shortDescription: string;
  clinicalHistory: string;
  clinicalPhoto: string;
  dermoscopicPhoto: string;
  location: string;
  ageGender: string;
  duration: string;
  evolution: string;
  groundTruthPathology: string;
  severity: 'low' | 'moderate' | 'high';
}

export interface QuizQuestion {
  id: number;
  questionText: string;
  description?: string;
  options: string[];
}

export interface AIAnalysisResult {
  topFindings: {
    diagnosis: string;
    probability: number;
    description: string;
    category: 'Malignant' | 'Benign' | 'Premalignant';
  }[];
  confidenceScore: number;
  confidenceTier: 'High Certainty' | 'Moderate Certainty' | 'Low Certainty';
  timelineInsight: string;
  clinicalAction: string;
  structuredPrompt: string;
}

export const PRESET_CASES: PresetCase[] = [
  {
    id: "case-882-d",
    name: "Case #882-D (Nodular Melanoma)",
    shortDescription: "Rapidly growing, elevated dark brown nodule with border irregularity.",
    clinicalHistory: "64-year-old male presents with a rapidly evolving, asymptomatic elevated dark lesion on the posterior thorax. First noticed ~18 months ago, but has significantly changed in color and height over the past month.",
    clinicalPhoto: "https://lh3.googleusercontent.com/aida-public/AB6AXuBNoTNxRAAL-k6XjwTMjZQ7_4EptjfvzZPYuCPwbFhZsLhP4aTSqk4gqP9U1ltVw-Uc8un8PQ3FPvy6EixvcFfHu0bYeG1zVIY2TQwmBZNFWFi3TpxCbvcRj4SmWWDja2YgJpOLkPjAQyEknPWThtIWnjA02dNKYv_olMphImf8VnURjrUR5CqIBZQT2plKdCCjyqds_wv3L6Z2L8JAAxvwA9NF5Qsy6RGFR1Xe9K1VVODRgvhx0FxGPTTtUFFF5UVwm95wSiO1W0c",
    dermoscopicPhoto: "https://lh3.googleusercontent.com/aida-public/AB6AXuAKwtbU7iDLcdjLKdHx52BgYMMWkHUSEl6J9pEfc57HH1t7u5hgolv0Y61kWzBr1O12ogT9MKxFfj_93Y0EGLbjCp7zEc6mNUvxczlIe_qDawQgh5xynkrouqukfGToczbYITCRAn8ZBDcjPzRpJY3YKG60NyDoPUFVmJRrJu_dRxzrYpvToa7fceInSCFcIV_isuwF-yC7RZkrDJkXUzfnittg_GGIuMvMVlxqn1Akudoy44qQLNPl0k8hKKijGifZfMTqUcQPpQo",
    location: "Posterior thorax (Upper Back)",
    ageGender: "64-year-old male",
    duration: "1-6 months",
    evolution: "Several changes",
    groundTruthPathology: "Nodular Melanoma (Breslow thickness 1.8mm)",
    severity: "high"
  },
  {
    id: "case-8214",
    name: "Case #8214 (Dysplastic Nevus)",
    shortDescription: "Asymmetric atypical pigmented plaque on hand.",
    clinicalHistory: "42-year-old female presents with an atypical erythematous plaque on the dorsal hand. She reports a history of frequent sun exposure and a maternal uncle with cutaneous melanoma.",
    clinicalPhoto: "https://lh3.googleusercontent.com/aida-public/AB6AXuAfQRlOdmGo64p8cesCvwafS9UDGfAnZrRMVdd76FMxnEa8GkDvuGIXanCIStzVuzSGq1nbn2Q9rdFjFLF_JHC8WKA_lxdf2BQPbEiKWAqaL97T0JwMV8GfnApcJsVKWjTjZkF_ydWWm8akCDxx0T3_CHZ2Fjrk2ixz4Eq7UoO9J36Jv_fh7-_b4acjTeKR4rPFZbxLjX9XErU-mHF4RChwrDIRK91nFQGx98rgQ54rHLl-rfHo_wQLVlYn59HNmCtXnBQNNTHn_Jk",
    dermoscopicPhoto: "https://lh3.googleusercontent.com/aida-public/AB6AXuDdcvgNv7CNZ56Sma15dp5rNvTkz-QVaAi8ZXyTUpog4vwUpNTk8mYkLJMBE5ZzBxgy7nkV2tICJCXYR966Ob5LvnbGkttO6X9SL_AKtxTBJHqWtmROzSyF1HPoPpyo8HBVwUg9KcAIsxdlM_FNbpS6K8xgslKkVHW893vaLT4U3Yx0JTUgplP7XWB3g1LSPtW1VJkCiAPMDHEgxDkYzxyKhZE-t1AKSlwHbvqjWnu0ej22RVYcGSZDk4J_vpL4f-xzKGh_CZi7lrw",
    location: "Dorsal skin of left hand",
    ageGender: "42-year-old female",
    duration: "1–4 weeks",
    evolution: "The color has changed",
    groundTruthPathology: "Severely Atypical Dysplastic Union Nevus",
    severity: "moderate"
  },
  {
    id: "case-304",
    name: "Case #304-B (Seborrheic Keratosis)",
    shortDescription: "Stuck-on waxy hyperpigmented papule with verrucous surface.",
    clinicalHistory: "57-year-old male with a waxy, hyperpigmented lesion on his flank. He describes it as having a 'stuck-on' appearance and states it has been unchanged for several years but occasionally gets irritated by his belt.",
    clinicalPhoto: "https://lh3.googleusercontent.com/aida-public/AB6AXuDMx_wGGUPdWZObFLApLfmbW91vut70sEHgS0mQoRNxcenY2wudWKSyE411IsQKk91kRfKhPy-yA2ySOugrYwDPYTsyVV7nhvDTAPIEPNrxxLc8g93dJ2G7tApg1TgMdcfnLyy_nl4HVB_x6Iq-hA6OHD2cxsYmNXOppkNA3TlScETh9RQBsGaAEO8HwNeWnDEEAr-4SIPxtyXgw-eDrXoduNpqae8BpzW6JOfuj9JtKHGCRCgmiA-nG96qcE2xOkCI0X2yCbCsEH0",
    dermoscopicPhoto: "https://lh3.googleusercontent.com/aida-public/AB6AXuBrxVpvTcgWNUaBKkYhofIj_TgAxA-EGeH02aZY5IPiEbLytykM7mHq_ITbW5JnVJVTQjZfNJs7BiDBS2qJSdbgm6vA3fS8kbji58V5bbqu-WZUJVZFurGfW0hxqYd-dqNSxpAPJnwu-d6QLpYzM8yH_nmnUKIeJtr0ndfc2xK8sopz-Yoj73mGrYeRC4JI5H7-r3hJrGTodKlP22QGthlleKdXdLEcXV6E6Zdc7Yy0PlTvPUTSlEumghOAmqzljSM_7DQe03ex5O8",
    location: "Right flank / abdomen",
    ageGender: "57-year-old male",
    duration: "More than 6 months",
    evolution: "No changes noticed",
    groundTruthPathology: "Benign Seborrheic Keratosis",
    severity: "low"
  }
];

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    id: 1,
    questionText: "How long have you noticed this?",
    description: "Temporal duration helps outline standard tumor growth speeds and distinguish acute vs. chronic lesions.",
    options: ["A few days", "1–4 weeks", "1–6 months", "More than 6 months", "I'm not sure"]
  },
  {
    id: 2,
    questionText: "Where is the lesion located?",
    description: "Anatomical distribution can narrow down dermatological differentials due to solar exposure or skin thickness.",
    options: ["Posterior thorax / Back", "Dorsal hand / Extremities", "Head / Neck", "Trunk / Abdomen", "Other skin fold"]
  },
  {
    id: 3,
    questionText: "Are there any associated physical symptoms?",
    description: "Symptoms like rapid enlargement or bleeding suggest aggressive growth or significant tissue degradation.",
    options: ["Asymptomatic (No symptoms)", "Mild pruritus / Itching", "Bleeding, oozing, or ulceration", "Mild tenderness / Pain", "Rapid physical enlargement only"]
  },
  {
    id: 4,
    questionText: "Is there a personal or family history of skin cancer?",
    description: "A positive family history of skin malignancies drastically shifts melanoma risk profiles.",
    options: ["Yes (Melanoma)", "Yes (Basal / Squamous Cell)", "Yes (Family history only)", "No history of skin cancer", "I am not sure"]
  },
  {
    id: 5,
    questionText: "Has it changed recently?",
    description: "Documenting the latest progression allows models to assess active mutation rate & structural disruption.",
    options: ["No changes noticed", "It seems to be growing", "The color has changed", "It's spreading to other areas", "Several multi-attribute changes"]
  }
];
