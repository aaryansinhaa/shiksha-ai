import React, { useState } from 'react';
import { Save, Code, Sliders } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const ProtocolEditor: React.FC = () => {
  const { language } = useChatStore();
  const [jsonText, setJsonText] = useState(JSON.stringify({
    name: "interview_default",
    title: "Shiksha AI Standard SRL Protocol",
    languages: ["en", "hi"],
    steps: [
      { id: "intro", type: "scenario", question_en: "What subject are you studying?", question_hi: "आप किस विषय की पढ़ाई कर रहे हैं?" },
      { id: "strategy", type: "open_question", question_en: "How do you prepare for a difficult exam?", question_hi: "आप किसी कठिन परीक्षा की तैयारी कैसे करते हैं?" },
      { id: "frequency", type: "likert_rating", min: 1, max: 5 },
      { id: "complete", type: "feedback_summary" }
    ]
  }, null, 2));

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            {language === 'hi' ? 'साक्षात्कार प्रोटोकॉल एडिटर' : 'Interview Protocol Editor'}
          </h2>
          <p className="text-sm text-slate-400">
            {language === 'hi' ? 'साक्षात्कार के चरणों एवं प्रश्नों का अनुकूलन (JSON Schema)' : 'Customize interview steps, scenarios, and prompts (JSON Schema)'}
          </p>
        </div>

        <button
          onClick={() => alert("Protocol Configuration Saved!")}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium shadow-lg transition-all text-sm"
        >
          <Save className="w-4 h-4" />
          <span>{language === 'hi' ? 'सहेजें' : 'Save Protocol'}</span>
        </button>
      </div>

      <div className="glass-panel p-4 rounded-2xl border border-slate-800">
        <textarea
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          rows={16}
          className="w-full bg-slate-900 font-mono text-sm text-indigo-300 p-4 rounded-xl border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>
  );
};
