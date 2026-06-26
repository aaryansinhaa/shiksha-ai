import React from 'react';
import { Search, Database, MousePointer, Cpu } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const ResearcherDashboard: React.FC = () => {
  const { language } = useChatStore();

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">
          {language === 'hi' ? 'अनुसंधान एवं टेलीमेट्री विश्लेषण' : 'Research Analytics & Behavioral Telemetry'}
        </h2>
        <p className="text-sm text-slate-400">
          {language === 'hi' ? 'माउस मूवमेंट ट्रेसेस, RAG वेक्टर दूरी एवं छात्र संवाद लॉग' : 'Sampled mouse traces, pgvector similarity logs, and raw transcript telemetry'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white">RAG Vector Matcher</h3>
          </div>
          <p className="text-xs text-slate-400">pgvector 768-dim L2 distance matching accuracy: 94.2%</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <MousePointer className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white">Mouse Trace Logging</h3>
          </div>
          <p className="text-xs text-slate-400">Active telemetry buffers: 100ms sampled (x, y, timestamp)</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white">Zimmerman Taxonomy</h3>
          </div>
          <p className="text-xs text-slate-400">14 strategy codes active across English & Hindi datasets</p>
        </div>
      </div>
    </div>
  );
};
