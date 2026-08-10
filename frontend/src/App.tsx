import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { ChatContainer } from './components/ChatContainer';
import { ConsentModal } from './components/ConsentModal';
import { TeacherDashboard } from './components/TeacherDashboard';
import { ResearcherDashboard } from './components/ResearcherDashboard';
import { ProtocolEditor } from './components/ProtocolEditor';
import { SurveyForm } from './components/SurveyForm';
import { ResultsView } from './components/ResultsView';
import { useChatStore } from './store/useChatStore';
import { useTelemetry } from './hooks/useTelemetry';

const queryClient = new QueryClient();

export const AppContent: React.FC = () => {
  const { hasConsent } = useChatStore();
  useTelemetry();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />
      {!hasConsent && <ConsentModal />}
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<ChatContainer />} />
          <Route path="/results" element={<ResultsView />} />
          <Route path="/teacher" element={<TeacherDashboard />} />
          <Route path="/researcher" element={<ResearcherDashboard />} />
          <Route path="/protocols" element={<ProtocolEditor />} />
          <Route path="/survey" element={<SurveyForm />} />
        </Routes>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppContent />
      </Router>
    </QueryClientProvider>
  );
};

export default App;
