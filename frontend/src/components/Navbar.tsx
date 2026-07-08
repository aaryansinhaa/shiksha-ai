import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, Languages, LayoutDashboard, MessageSquare, BookOpen, BarChart3, Award } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const Navbar: React.FC = () => {
  const { language, setLanguage } = useChatStore();
  const location = useLocation();

  const navLinks = [
    { path: '/', label_en: 'AI Chat', label_hi: 'AI चैट', icon: MessageSquare },
    { path: '/results', label_en: 'SRL Profile Report', label_hi: 'परिणाम रिपोर्ट', icon: Award },
    { path: '/teacher', label_en: 'Teacher Dashboard', label_hi: 'शिक्षक डैशबोर्ड', icon: LayoutDashboard },
    { path: '/researcher', label_en: 'Research & Telemetry', label_hi: 'अनुसंधान एवं टेलीमेट्री', icon: BarChart3 },
    { path: '/protocols', label_en: 'Protocol Editor', label_hi: 'प्रोटोकॉल एडिटर', icon: BookOpen },
  ];

  return (
    <header className="sticky top-0 z-40 glass-panel border-b border-slate-800 px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Shiksha AI
            </h1>
            <p className="text-xs text-indigo-400 font-medium">GenAI & RAG Learning Assessor</p>
          </div>
        </Link>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{language === 'hi' ? link.label_hi : link.label_en}</span>
              </Link>
            );
          })}
        </nav>

        {/* Language Switcher Button */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
            <button
              onClick={() => setLanguage('en')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                language === 'en'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              English
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                language === 'hi'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              हिन्दी
            </button>
          </div>
        </div>

      </div>
    </header>
  );
};
