import { AlertTriangle, ArrowRight, Brain, ShieldAlert } from "lucide-react";
import { motion } from "motion/react";

interface LandingPageProps {
  onBegin: () => void;
}

export default function LandingPage({ onBegin }: LandingPageProps) {
  const steps = [
    {
      num: 1,
      title: "Choose Image",
      desc: "Select clinical / macroscopic photo or dermoscopic / magnified lesion image before upload.",
      visual: (
        <div className="mt-auto overflow-hidden rounded-lg">
          <img 
            className="w-full h-32 object-cover grayscale opacity-60 hover:grayscale-0 hover:opacity-100 transition-all duration-500" 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBrxVpvTcgWNUaBKkYhofIj_TgAxA-EGeH02aZY5IPiEbLytykM7mHq_ITbW5JnVJVTQjZfNJs7BiDBS2qJSdbgm6vA3fS8kbji58V5bbqu-WZUJVZFurGfW0hxqYd-dqNSxpAPJnwu-d6QLpYzM8yH_nmnUKIeJtr0ndfc2xK8sopz-Yoj73mGrYeRC4JI5H7-r3hJrGTodKlP22QGthlleKdXdLEcXV6E6Zdc7Yy0PlTvPUTSlEumghOAmqzljSM_7DQe03ex5O8" 
            alt="Dermatoscopic learning image" 
          />
        </div>
      )
    },
    {
      num: 2,
      title: "Add Context",
      desc: "Upload an image and add non-identifying context for an educational review workflow.",
      visual: (
        <div className="mt-auto flex flex-col gap-2">
          <div className="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
            <div className="bg-brand-accent h-full w-1/3"></div>
          </div>
          <span className="font-sans text-xs font-semibold uppercase tracking-wider text-brand-accent">
            Metadata Integration
          </span>
        </div>
      )
    },
    {
      num: 3,
      title: "Review Case",
      desc: "Generate educational model output for guided reflection, not diagnosis or treatment advice.",
      visual: (
        <div className="mt-auto h-32 flex items-center justify-center bg-brand-primary rounded-lg relative overflow-hidden">
          <div className="absolute inset-0 opacity-45 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-brand-accent via-transparent to-transparent"></div>
          <Brain className="text-white w-12 h-12 relative z-10 animate-pulse" />
        </div>
      )
    },
    {
      num: 4,
      title: "Review Output",
      desc: "Compare educational model output with the provided learning case context and safety notes.",
      visual: (
        <div className="mt-auto space-y-2">
          <div className="flex justify-between items-center bg-brand-secondary p-2 rounded border border-gray-100">
            <span className="font-sans text-[11px] font-bold text-gray-400 uppercase">Output Type</span>
            <span className="text-brand-accent font-bold text-sm">Mock</span>
          </div>
          <div className="flex justify-between items-center bg-brand-secondary p-2 rounded border border-gray-100">
            <span className="font-sans text-[11px] font-bold text-gray-400 uppercase">Use</span>
            <span className="text-brand-accent font-bold text-sm">Learning</span>
          </div>
        </div>
      )
    }
  ];

  return (
    <main className="pt-28 pb-20 px-6 md:px-10 max-w-[1440px] mx-auto min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-brand-secondary" id="landing-page-container">
      {/* Abstract Background Shapes */}
      <div className="absolute -top-40 -right-40 w-[600px] h-[600px] bg-brand-accent-light opacity-30 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-sky-200 opacity-20 blur-[100px] rounded-full pointer-events-none"></div>

      {/* Hero Headline & Subtitle */}
      <div className="text-center mb-16 relative z-10 max-w-3xl">
        <motion.h1 
          className="font-serif text-4xl md:text-5xl lg:text-6xl text-brand-primary font-bold tracking-tight mb-6"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          id="landing-headline"
        >
          Experimental dermatology AI learning lab
        </motion.h1>
        <motion.p 
          className="font-serif text-lg md:text-xl text-gray-600 italic mb-8 max-w-2xl mx-auto leading-relaxed"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          id="landing-subheading"
        >
          A prototype space for educational review of dermatology image workflows and model-output literacy.
        </motion.p>
        
        <motion.div 
          className="inline-flex items-center gap-2 bg-red-50 text-red-800 px-5 py-2.5 rounded-full border border-red-100 shadow-sm"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.5, type: "spring" }}
          id="disclaimer-badge"
        >
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <span className="font-sans text-xs font-bold uppercase tracking-wider">
            Model output, not diagnosis. For educational review only.
          </span>
        </motion.div>
      </div>

      {/* Learning Journey Roadmap */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full mb-16 relative z-10" id="roadmap-grid">
        {steps.map((step, i) => (
          <motion.div 
            key={step.num}
            className="bg-white p-8 rounded-xl border border-gray-200/60 shadow-sm hover-lift flex flex-col min-h-[340px]"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i + 0.5, duration: 0.6 }}
            id={`step-card-${step.num}`}
          >
            <div className="w-12 h-12 bg-indigo-50 text-brand-primary rounded-full flex items-center justify-center mb-6 font-serif text-lg font-bold">
              {step.num}
            </div>
            <h3 className="font-serif text-xl font-bold text-brand-primary mb-3">{step.title}</h3>
            <p className="font-sans text-sm text-gray-500 leading-relaxed mb-6">{step.desc}</p>
            {step.visual}
          </motion.div>
        ))}
      </div>

      {/* Primary CTA */}
      <motion.div 
        className="relative z-10 flex flex-col items-center gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.1, duration: 0.8 }}
        id="cta-holder"
      >
        <button 
          onClick={onBegin}
          className="bg-brand-primary text-white font-serif text-lg md:text-xl px-12 py-5 rounded-full hover:bg-opacity-95 hover:shadow-xl hover:-translate-y-0.5 active:scale-95 flex items-center gap-4 transition-all group cursor-pointer"
          id="btn-begin-case"
        >
          Begin learning case
          <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform duration-300" />
        </button>
        <p className="font-sans text-[11px] font-bold text-gray-400 tracking-widest uppercase">
          No account required for educational modules
        </p>
      </motion.div>
    </main>
  );
}
