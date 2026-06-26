import React from 'react';
import { ClipboardList, CheckCircle } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const SurveyForm: React.FC = () => {
  const { language } = useChatStore();

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">
          {language === 'hi' ? 'SRL-O अध्ययन रणनीति प्रश्नोत्तरी' : 'SRL-O Strategy Survey Questionnaire'}
        </h2>
        <p className="text-sm text-slate-400">Post-interview quantitative evaluation</p>
      </div>

      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-200">
            1. {language === 'hi' ? 'मैं अध्ययन सत्र शुरू करने से पहले स्पष्ट लक्ष्य निर्धारित करता हूँ।' : 'I set clear goals before starting a study session.'}
          </p>
          <div className="flex gap-4">
            {[1, 2, 3, 4, 5].map((val) => (
              <label key={val} className="flex items-center gap-1.5 text-xs text-slate-400">
                <input type="radio" name="q1" value={val} className="accent-indigo-600" />
                <span>{val}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-200">
            2. {language === 'hi' ? 'मैं नोट्स और माइंड मैप बनाकर कठिन अवधारणाओं को समझता हूँ।' : 'I create summary notes or mind maps to understand complex concepts.'}
          </p>
          <div className="flex gap-4">
            {[1, 2, 3, 4, 5].map((val) => (
              <label key={val} className="flex items-center gap-1.5 text-xs text-slate-400">
                <input type="radio" name="q2" value={val} className="accent-indigo-600" />
                <span>{val}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={() => alert("Survey Submitted Successfully!")}
          className="py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl text-sm"
        >
          {language === 'hi' ? 'उत्तर जमा करें' : 'Submit Survey'}
        </button>
      </div>
    </div>
  );
};
