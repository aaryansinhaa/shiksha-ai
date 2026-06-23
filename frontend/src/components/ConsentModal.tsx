import React from 'react';
import { ShieldCheck, CheckCircle2 } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const ConsentModal: React.FC = () => {
  const { language, setHasConsent } = useChatStore();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel max-w-lg w-full rounded-2xl p-6 shadow-2xl border border-slate-700/50 animate-in fade-in zoom-in duration-300">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">
              {language === 'hi' ? 'सहमति एवं गोपनीयता नीति' : 'Informed Consent & Privacy'}
            </h2>
            <p className="text-xs text-slate-400">Shiksha AI Educational Assessment</p>
          </div>
        </div>

        <div className="space-y-3 text-sm text-slate-300 mb-6 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
          {language === 'hi' ? (
            <>
              <p>शिक्षा AI साक्षात्कार में भाग लेने के लिए आपका स्वागत है।</p>
              <p>• आपका संवाद पूरी तरह से सुरक्षित है और केवल आपकी अध्ययन रणनीतियों का विश्लेषण करने के लिए उपयोग किया जाता है।</p>
              <p>• माउस मूवमेंट और सहभागिता का उपयोग शोध उद्देश्यों के लिए गुमनाम रूप से किया जाता है।</p>
            </>
          ) : (
            <>
              <p>Welcome to the Shiksha AI Learning Strategy Assessment.</p>
              <p>• Your conversation turns are processed to analyze your Self-Regulated Learning (SRL) techniques.</p>
              <p>• Telemetry and mouse traces are collected anonymously for educational research optimization.</p>
            </>
          )}
        </div>

        <button
          onClick={() => setHasConsent(true)}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25 transition-all"
        >
          <CheckCircle2 className="w-5 h-5" />
          <span>{language === 'hi' ? 'मैं सहमत हूँ और शुरू करें' : 'I Agree & Start Assessment'}</span>
        </button>
      </div>
    </div>
  );
};
