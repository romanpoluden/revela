import { Bell, UserCircle } from "lucide-react";

interface TopNavBarProps {
  onNavigateHome: () => void;
  onNavigateWorkbench: () => void;
  activeTab: string;
}

export default function TopNavBar({ onNavigateHome, onNavigateWorkbench, activeTab }: TopNavBarProps) {
  return (
    <nav className="bg-white border-b border-gray-200 fixed top-0 w-full z-50 shadow-sm transition-colors duration-200">
      <div className="flex justify-between items-center px-6 md:px-10 py-4 w-full max-w-[1440px] mx-auto">
        <div className="flex items-center gap-8">
          <span 
            className="font-serif text-2xl font-bold text-brand-primary cursor-pointer hover:opacity-85 select-none"
            onClick={onNavigateHome}
            id="brand-logo"
          >
            Revela
          </span>
          <div className="hidden md:flex space-x-6">
            <button 
              onClick={onNavigateHome}
              className={`text-sm font-semibold tracking-wider transition-all duration-200 cursor-pointer ${
                activeTab === 'home' 
                  ? 'text-brand-accent border-b-2 border-brand-accent pb-1' 
                  : 'text-gray-500 hover:text-brand-primary'
              }`}
              id="nav-curriculum"
            >
              Curriculum
            </button>
            <button 
              className="text-gray-500 hover:text-brand-primary text-sm font-semibold tracking-wider transition-colors cursor-pointer"
              id="nav-case-library"
            >
              Case Library
            </button>
            <button 
              onClick={onNavigateWorkbench}
              className={`text-sm font-semibold tracking-wider transition-all duration-200 cursor-pointer ${
                activeTab === 'workbench' 
                  ? 'text-brand-accent border-b-2 border-brand-accent pb-1' 
                  : 'text-gray-500 hover:text-brand-primary'
              }`}
            id="nav-ai-workbench"
          >
              AI Learning Lab
            </button>
            <button 
              className="text-gray-500 hover:text-brand-primary text-sm font-semibold tracking-wider transition-colors cursor-pointer"
              id="nav-community"
            >
              Community
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button 
            className="text-gray-500 hover:text-brand-primary cursor-pointer transition-all duration-200 p-1 rounded-full hover:bg-gray-100"
            id="btn-notifications"
          >
            <Bell className="w-5 h-5" />
          </button>
          <button 
            className="text-gray-500 hover:text-brand-primary cursor-pointer transition-all duration-200 p-1 rounded-full hover:bg-gray-100"
            id="btn-account"
          >
            <UserCircle className="w-6 h-6" />
          </button>
          <button 
            onClick={onNavigateWorkbench}
            className="bg-brand-primary text-white text-xs font-semibold tracking-wider uppercase px-6 py-2 rounded-lg hover:bg-opacity-90 transition-all active:scale-95 cursor-pointer shadow-sm"
            id="btn-start-analysis"
          >
            Start Review
          </button>
        </div>
      </div>
    </nav>
  );
}
