/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import TopNavBar from "./components/TopNavBar";
import LandingPage from "./components/LandingPage";
import DiagnosticWorkbench from "./components/DiagnosticWorkbench";

export default function App() {
  const [currentPage, setCurrentPage] = useState<'home' | 'workbench'>('home');

  return (
    <div className="min-h-screen bg-brand-secondary selection:bg-brand-accent/20 selección:text-brand-primary">
      {/* Shared Navigation Header */}
      <TopNavBar 
        onNavigateHome={() => setCurrentPage('home')}
        onNavigateWorkbench={() => setCurrentPage('workbench')}
        activeTab={currentPage}
      />

      {/* Primary Workspace Pages Container */}
      <div className="transition-all duration-300">
        {currentPage === 'home' ? (
          <LandingPage onBegin={() => setCurrentPage('workbench')} />
        ) : (
          <div className="pt-16">
            <DiagnosticWorkbench />
          </div>
        )}
      </div>
    </div>
  );
}
