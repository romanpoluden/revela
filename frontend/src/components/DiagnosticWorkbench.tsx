import React, { useState, useRef } from "react";
import { 
  FileText, Layers, Upload, Microscope, HelpCircle, Settings, Plus,
  ChevronRight, ArrowLeft, ArrowRight, CheckCircle, AlertTriangle, Terminal, 
  Copy, Check, Info, ShieldAlert, Award, Eye, BarChart2, Mail, Loader2
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { IMAGE_WORKFLOWS, QUIZ_QUESTIONS, ImageWorkflow, AIAnalysisResult } from "../types";
import { analyzeCase, InferenceClientError } from "../lib/inferenceClient";

export default function DiagnosticWorkbench() {
  // Navigation / View states
  // 'selection' | 'questionnaire' | 'analyzing' | 'results' | 'error'
  const [sessionState, setSessionState] = useState<'selection' | 'questionnaire' | 'analyzing' | 'results' | 'error'>('selection');
  
  // Selected image workflow and uploaded image state
  const [selectedWorkflow, setSelectedWorkflow] = useState<ImageWorkflow>(IMAGE_WORKFLOWS[0]);
  const [customImage, setCustomImage] = useState<string | null>(null);
  const [customImageFile, setCustomImageFile] = useState<File | null>(null);
  const [uploadedImageName, setUploadedImageName] = useState<string | null>(null);
  
  // Multi-step quiz state
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({
    1: "1–4 weeks",
    2: "Posterior thorax / Back",
    3: "Asymptomatic (No symptoms)",
    4: "No history of skin cancer",
    5: "The color has changed"
  });

  // Frontend mock review states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AIAnalysisResult | null>(null);
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [waitlistEmail, setWaitlistEmail] = useState("");
  const [waitlistSuccess, setWaitlistSuccess] = useState(false);
  const [isSubmittingWaitlist, setIsSubmittingWaitlist] = useState(false);
  const [reviewMode, setReviewMode] = useState<string>("educational-simulation");
  const [inferenceError, setInferenceError] = useState<string | null>(null);

  // Drag and Drop Ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleWorkflowSelect = (workflow: ImageWorkflow) => {
    setSelectedWorkflow(workflow);
    setAnalysisResult(null);
    setInferenceError(null);
    setCurrentQuizIndex(0);
  };

  // Custom File upload handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setCustomImage(reader.result as string);
        setCustomImageFile(file);
        setUploadedImageName(file.name);
        setInferenceError(null);
        setCurrentQuizIndex(0);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setCustomImage(reader.result as string);
        setCustomImageFile(file);
        setUploadedImageName(file.name);
        setInferenceError(null);
        setCurrentQuizIndex(0);
      };
      reader.readAsDataURL(file);
    }
  };

  // Quiz progression
  const handleQuizOptionSelect = (option: string) => {
    const activeQuestion = QUIZ_QUESTIONS[currentQuizIndex];
    setQuizAnswers(prev => ({
      ...prev,
      [activeQuestion.id]: option
    }));
  };

  const handleQuizNext = () => {
    if (currentQuizIndex < QUIZ_QUESTIONS.length - 1) {
      setCurrentQuizIndex(prev => prev + 1);
    } else {
      // Trigger educational model output
      handleInitiateAnalysis();
    }
  };

  const handleQuizBack = () => {
    if (currentQuizIndex > 0) {
      setCurrentQuizIndex(prev => prev - 1);
    } else {
      setSessionState('selection');
    }
  };

  // Frontend-only analysis handler. Production inference will use the HF backend API client.
  const handleInitiateAnalysis = async (forceMock = false) => {
    setSessionState('analyzing');
    setIsAnalyzing(true);
    setInferenceError(null);
    
    try {
      const data = await analyzeCase({
        workflow: selectedWorkflow,
        answers: quizAnswers,
        customImage,
        imageFile: customImageFile,
        forceMock,
      });

      setAnalysisResult(data.analysis);
      setReviewMode(data.mode);
    } catch (e) {
      console.error("Inference request failed.", e);
      if (e instanceof InferenceClientError) {
        setInferenceError(
          e.code === "missing_image"
            ? "Upload an image before requesting live educational model output, or continue with demo mode."
            : "Live model output is currently unavailable. You can continue with demo mode or try again later.",
        );
        setSessionState('error');
        return;
      }

      setInferenceError("Educational model output is currently unavailable. You can continue with demo mode or try again later.");
      setSessionState('error');
      return;
    } finally {
      setIsAnalyzing(false);
    }

    setSessionState('results');
  };

  // Clipboard copy helper
  const handleCopyPromptText = () => {
    if (analysisResult) {
      navigator.clipboard.writeText(analysisResult.structuredPrompt);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2000);
    }
  };

  // Waitlist form helper
  const handleWaitlistSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!waitlistEmail || !waitlistEmail.includes("@")) return;
    
    setIsSubmittingWaitlist(true);
    setTimeout(() => {
      setIsSubmittingWaitlist(false);
      setWaitlistSuccess(true);
      setWaitlistEmail("");
    }, 1500);
  };

  // Restart learning workflow
  const handleResetWorkflow = () => {
    setCustomImage(null);
    setCustomImageFile(null);
    setUploadedImageName(null);
    setSelectedWorkflow(IMAGE_WORKFLOWS[0]);
    setAnalysisResult(null);
    setInferenceError(null);
    setQuizAnswers({
      1: "1–4 weeks",
      2: "Posterior thorax / Back",
      3: "Asymptomatic (No symptoms)",
      4: "No history of skin cancer",
      5: "The color has changed"
    });
    setCurrentQuizIndex(0);
    setSessionState('selection');
  };

  return (
    <div className="flex min-h-screen text-brand-primary h-screen overflow-hidden font-sans placeholder:text-gray-300">
      
      {/* SideNavBar - Resident Portal Left Menu */}
      <aside className="hidden md:flex flex-col w-[280px] h-full bg-brand-primary text-gray-300 border-r border-gray-800 p-4 shrink-0 transition-all z-20" id="workbench-sidebar">
        <div className="px-3 py-6 border-b border-gray-800 mb-6 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-500/15 flex items-center justify-center border border-indigo-500/20">
            <Microscope className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-white font-semibold text-sm tracking-wide leading-tight">Resident Portal</h2>
            <p className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Educational AI Suite</p>
          </div>
        </div>

        {/* Sidebar Navigation */}
        <nav className="flex-1 space-y-1">
          <button 
            onClick={handleResetWorkflow}
            className={`w-full flex items-center gap-3 px-4 py-3 text-xs font-semibold uppercase tracking-wider rounded-lg transition-all cursor-pointer ${
              sessionState === 'selection' ? 'bg-gray-800/60 text-white font-bold' : 'hover:bg-gray-800/40 hover:text-white'
            }`}
          >
            <Layers className="w-4 h-4" />
            Image Selection
          </button>
          
          <button 
            onClick={() => {
              if (sessionState !== 'selection') setSessionState('questionnaire');
            }}
            disabled={sessionState === 'selection'}
            className={`w-full flex items-center gap-3 px-4 py-3 text-xs font-semibold uppercase tracking-wider rounded-lg transition-all cursor-pointer disabled:opacity-50 ${
              sessionState === 'questionnaire' ? 'bg-gray-800/60 text-white font-bold' : 'hover:bg-gray-800/40 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" />
            Case Context
          </button>

          <button 
            onClick={() => {
              if (analysisResult) setSessionState('results');
            }}
            disabled={!analysisResult}
            className={`w-full flex items-center gap-3 px-4 py-3 text-xs font-semibold uppercase tracking-wider rounded-lg transition-all cursor-pointer disabled:opacity-50 ${
              sessionState === 'results' ? 'bg-gray-800/60 text-white font-bold' : 'hover:bg-gray-800/40 hover:text-white'
            }`}
          >
            <Award className="w-4 h-4" />
            Output Summary
          </button>
        </nav>

        {/* Bottom actions */}
        <div className="pt-4 border-t border-gray-800 space-y-3">
          <button 
            onClick={handleResetWorkflow}
            className="w-full bg-white text-brand-primary text-xs font-bold uppercase py-3.5 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-gray-100 transition-all active:scale-95 cursor-pointer shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Review
          </button>
          
          <a href="#" className="flex items-center gap-3 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-gray-400 hover:text-white transition-colors">
            <HelpCircle className="w-4 h-4" />
            Help & Docs
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-gray-400 hover:text-white transition-colors">
            <Settings className="w-4 h-4" />
            Settings
          </a>
        </div>
      </aside>

      {/* Main Workspace Frame */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-brand-secondary">
        
        {/* Scrollable Workflow Arena */}
        <div className="flex-grow overflow-y-auto px-6 md:px-10 py-8 custom-scroll">
          <div className="max-w-[1100px] mx-auto">
            
            <AnimatePresence mode="wait">
              {/* VIEW 1: Selection & Image Upload */}
              {sessionState === 'selection' && (
                <motion.div 
                  key="selection"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-10"
                >
                  {/* Page Intro */}
                  <header>
                    <h2 className="font-serif text-3xl font-bold tracking-tight text-brand-primary mb-1">Educational Review Workflow</h2>
                    <p className="text-sm text-gray-500 max-w-2xl">Prototype image workflow for educational review only. Select the uploaded image mode before upload. This is not diagnosis or treatment advice.</p>
                  </header>

                  {/* Workflow Selection */}
                  <section>
                    <div className="flex items-center justify-between mb-5">
                      <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400">1. Select image workflow</h3>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {IMAGE_WORKFLOWS.map((workflow) => {
                        const isSelected = selectedWorkflow.id === workflow.id;
                        return (
                          <button
                            key={workflow.id}
                            onClick={() => handleWorkflowSelect(workflow)}
                            className={`text-left p-5 rounded-xl border transition-all cursor-pointer hover:-translate-y-0.5 ${
                              isSelected
                                ? "border-brand-primary bg-white shadow-lg ring-2 ring-brand-accent-light"
                                : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-md"
                            }`}
                          >
                            <div className="flex items-start gap-4">
                              <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${isSelected ? "bg-brand-primary text-white" : "bg-surface-low text-brand-primary"}`}>
                                <Microscope className="w-6 h-6" />
                              </div>
                              <div>
                                <p className="font-serif text-xl font-bold text-brand-primary mb-1">{workflow.label}</p>
                                <p className="text-sm text-gray-500 leading-relaxed">{workflow.description}</p>
                                <p className="mt-3 text-[11px] uppercase tracking-widest text-brand-accent font-bold">{workflow.model_id}</p>
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </section>

                  {/* Upload Area */}
                  <section>
                    <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-5">2. Upload image</h3>
                    <div 
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      className="bg-white border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center cursor-pointer hover:border-brand-accent hover:bg-brand-secondary transition-colors"
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/webp"
                        className="hidden"
                        onChange={handleFileUpload}
                      />
                      {customImage ? (
                        <div className="space-y-4">
                          <img src={customImage} alt="Uploaded preview" className="max-h-72 mx-auto rounded-xl shadow-md object-contain" />
                          <div>
                            <p className="font-bold text-brand-primary">{uploadedImageName || "Uploaded image"}</p>
                            <p className="text-xs text-gray-500 mt-1">Click or drag another image to replace.</p>
                          </div>
                        </div>
                      ) : (
                        <div className="py-8">
                          <Upload className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                          <p className="font-serif text-2xl font-bold text-brand-primary mb-2">Upload an educational demo image</p>
                          <p className="text-sm text-gray-500">PNG, JPG, JPEG, or WEBP. Image is used only for this prototype review flow.</p>
                        </div>
                      )}
                    </div>
                  </section>

                  <div className="flex justify-end">
                    <button
                      onClick={() => setSessionState('questionnaire')}
                      className="bg-brand-primary text-white text-xs font-bold uppercase tracking-wider px-8 py-3.5 rounded-lg hover:bg-opacity-95 transition-all active:scale-95 cursor-pointer flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={!customImageFile && !customImage}
                    >
                      Continue to context
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              )}

              {/* VIEW 2: Questionnaire */}
              {sessionState === 'questionnaire' && (
                <motion.div
                  key="questionnaire"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="h-[calc(100vh-4rem)] flex flex-col"
                >
                  <div className="bg-white rounded-xl border border-gray-200 shadow-md overflow-hidden flex flex-col flex-1">
                    <div className="p-8 border-b border-gray-100 shrink-0">
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Question {currentQuizIndex + 1} of {QUIZ_QUESTIONS.length}</span>
                        <span className="text-xs font-bold uppercase tracking-widest text-brand-accent">{Math.round(((currentQuizIndex + 1) / QUIZ_QUESTIONS.length) * 100)}% Complete</span>
                      </div>
                      <div className="h-2 bg-indigo-50 rounded-full overflow-hidden">
                        <div className="h-full bg-brand-primary transition-all duration-500" style={{ width: `${((currentQuizIndex + 1) / QUIZ_QUESTIONS.length) * 100}%` }}></div>
                      </div>
                    </div>

                    <div className="p-8 flex-1 overflow-y-auto custom-scroll">
                      <h2 className="font-serif text-4xl font-bold text-brand-primary mb-4">{QUIZ_QUESTIONS[currentQuizIndex].question}</h2>
                      <p className="text-gray-400 text-sm mb-8">{QUIZ_QUESTIONS[currentQuizIndex].subtitle}</p>
                      
                      <div className="space-y-3">
                        {QUIZ_QUESTIONS[currentQuizIndex].options.map((option) => (
                          <button
                            key={option}
                            onClick={() => handleQuizOptionSelect(option)}
                            className={`w-full text-left p-4 rounded-lg border flex items-center justify-between transition-all cursor-pointer ${
                              quizAnswers[QUIZ_QUESTIONS[currentQuizIndex].id] === option
                                ? "border-brand-primary ring-2 ring-brand-primary bg-surface-low"
                                : "border-gray-200 bg-white hover:border-brand-accent"
                            }`}
                          >
                            <span className="text-sm font-medium text-gray-700">{option}</span>
                            <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${quizAnswers[QUIZ_QUESTIONS[currentQuizIndex].id] === option ? "border-brand-primary" : "border-gray-300"}`}>
                              {quizAnswers[QUIZ_QUESTIONS[currentQuizIndex].id] === option && <span className="w-2.5 h-2.5 rounded-full bg-brand-primary"></span>}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-between items-center shrink-0">
                      <button
                        onClick={handleQuizBack}
                        className="px-6 py-3 rounded-lg border border-gray-300 text-gray-500 text-xs font-bold uppercase tracking-wider hover:bg-white transition-colors cursor-pointer flex items-center gap-2"
                      >
                        <ArrowLeft className="w-4 h-4" />
                        Back
                      </button>
                      <button
                        onClick={handleQuizNext}
                        className="px-8 py-3 rounded-lg bg-brand-primary text-white text-xs font-bold uppercase tracking-wider hover:bg-opacity-95 transition-all cursor-pointer flex items-center gap-2"
                      >
                        {currentQuizIndex === QUIZ_QUESTIONS.length - 1 ? "Review Model Output" : "Continue"}
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* VIEW 3: Analyzing */}
              {sessionState === 'analyzing' && (
                <motion.div
                  key="analyzing"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="min-h-[70vh] flex items-center justify-center"
                >
                  <div className="text-center max-w-md">
                    <div className="w-20 h-20 bg-brand-primary rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl">
                      <Loader2 className="w-10 h-10 text-white animate-spin" />
                    </div>
                    <h2 className="font-serif text-3xl font-bold text-brand-primary mb-3">Generating educational model output</h2>
                    <p className="text-gray-500 leading-relaxed">Running the selected image workflow and preparing a safety-framed review. This is not diagnosis.</p>
                  </div>
                </motion.div>
              )}

              {/* VIEW 4: Error */}
              {sessionState === 'error' && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.3 }}
                  className="min-h-[70vh] flex items-center justify-center"
                >
                  <div className="max-w-xl bg-white border border-red-100 rounded-2xl shadow-lg p-8 text-center">
                    <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
                      <AlertTriangle className="w-7 h-7 text-red-600" />
                    </div>
                    <h2 className="font-serif text-3xl font-bold text-brand-primary mb-3">Live model output unavailable</h2>
                    <p className="text-gray-500 leading-relaxed mb-6">{inferenceError}</p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <button
                        onClick={() => setSessionState('selection')}
                        className="px-6 py-3 rounded-lg border border-gray-300 text-gray-600 text-xs font-bold uppercase tracking-wider hover:bg-gray-50 transition-colors cursor-pointer"
                      >
                        Back to upload
                      </button>
                      <button
                        onClick={() => handleInitiateAnalysis(true)}
                        className="px-6 py-3 rounded-lg bg-brand-primary text-white text-xs font-bold uppercase tracking-wider hover:bg-opacity-95 transition-colors cursor-pointer"
                      >
                        Continue with demo mode
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* VIEW 5: Results */}
              {sessionState === 'results' && analysisResult && (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  {/* Results Header */}
                  <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-50 text-green-700 text-[11px] uppercase tracking-widest font-bold mb-3">
                        <CheckCircle className="w-3.5 h-3.5" />
                        Educational Output Ready
                      </div>
                      <h2 className="font-serif text-4xl font-bold text-brand-primary">Model output summary</h2>
                      <p className="text-gray-500 mt-2">Review educational model output, uncertainty, and safety notes.</p>
                    </div>
                    <button
                      onClick={handleResetWorkflow}
                      className="bg-white border border-gray-200 text-brand-primary px-5 py-3 rounded-lg text-xs font-bold uppercase tracking-wider hover:bg-gray-50 cursor-pointer flex items-center gap-2 shadow-sm"
                    >
                      <Plus className="w-4 h-4" />
                      New review
                    </button>
                  </div>

                  {/* Result Grid */}
                  <div className="grid lg:grid-cols-[1.2fr_0.8fr] gap-6 items-start">
                    {/* Left: Model Output */}
                    <section className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                      <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                        <div>
                          <h3 className="font-serif text-2xl font-bold text-brand-primary">Top educational output</h3>
                          <p className="text-xs text-gray-400 mt-1 uppercase tracking-widest">{reviewMode === "hf-live" ? "Live HF Backend" : "Demo Mode"}</p>
                        </div>
                        <div className="w-14 h-14 rounded-2xl bg-brand-primary text-white flex items-center justify-center">
                          <BarChart2 className="w-7 h-7" />
                        </div>
                      </div>

                      <div className="p-6 space-y-5">
                        <div className="rounded-2xl bg-brand-secondary border border-gray-100 p-5">
                          <div className="flex justify-between gap-4 items-start">
                            <div>
                              <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-2">Top output</p>
                              <h4 className="font-serif text-3xl font-bold text-brand-primary">{analysisResult.topFindings[0]?.label}</h4>
                              <p className="text-sm text-gray-500 mt-2 max-w-2xl">{analysisResult.topFindings[0]?.description}</p>
                            </div>
                            <div className="text-right shrink-0">
                              <p className="text-4xl font-serif font-bold text-brand-accent">{analysisResult.confidenceScore.toFixed(1)}%</p>
                              <p className="text-[10px] uppercase tracking-widest text-gray-400 font-bold mt-1">Model confidence</p>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Top-k outputs</h4>
                          <div className="space-y-3">
                            {analysisResult.topFindings.map((finding, index) => (
                              <div key={`${finding.label}-${index}`} className="flex items-center gap-4">
                                <div className="w-8 text-xs font-bold text-gray-400">#{index + 1}</div>
                                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                                  <div className="h-full bg-brand-primary" style={{ width: `${Math.max(3, finding.probability)}%` }}></div>
                                </div>
                                <div className="w-28 text-right text-xs text-gray-500 font-semibold">{finding.probability.toFixed(1)}%</div>
                              </div>
                            ))}
                          </div>
                        </div>

                      