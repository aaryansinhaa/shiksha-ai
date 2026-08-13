import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { Save, Download, Upload, Trash2, Plus, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

interface ProtocolItem {
  name: string;
  title: string;
  languages: string[];
  steps: any;
}

export const ProtocolEditor: React.FC = () => {
  const { language } = useChatStore();
  const [protocols, setProtocols] = useState<ProtocolItem[]>([]);
  const [selectedName, setSelectedName] = useState<string>('interview_default');
  const [jsonText, setJsonText] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchProtocols();
  }, []);

  const fetchProtocols = async () => {
    try {
      setLoading(true);
      const resp = await axios.get('/protocols');
      if (resp.data && Array.isArray(resp.data)) {
        setProtocols(resp.data);
        if (resp.data.length > 0) {
          const current = resp.data.find((p: ProtocolItem) => p.name === selectedName) || resp.data[0];
          setSelectedName(current.name);
          setJsonText(JSON.stringify(current, null, 2));
        }
      }
    } catch (err) {
      showStatus('error', language === 'hi' ? 'प्रोटोकॉल लोड करने में विफल' : 'Failed to load protocols from server');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProtocol = (name: string) => {
    setSelectedName(name);
    const target = protocols.find(p => p.name === name);
    if (target) {
      setJsonText(JSON.stringify(target, null, 2));
    }
  };

  const showStatus = (type: 'success' | 'error', text: string) => {
    setStatusMessage({ type, text });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(jsonText);
      if (!parsed.name || !parsed.title) {
        showStatus('error', language === 'hi' ? 'प्रोटोकॉल में name तथा title होना आवश्यक है' : 'Protocol must contain name and title fields');
        return;
      }

      const isExisting = protocols.some(p => p.name === parsed.name);
      if (isExisting) {
        await axios.put(`/protocols/${parsed.name}`, parsed);
        showStatus('success', language === 'hi' ? 'प्रोटोकॉल सफलतापूर्वक सहेजा गया' : `Protocol '${parsed.name}' updated successfully`);
      } else {
        await axios.post('/protocols', parsed);
        showStatus('success', language === 'hi' ? 'नया प्रोटोकॉल बनाया गया' : `New protocol '${parsed.name}' created successfully`);
      }
      fetchProtocols();
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message;
      showStatus('error', `${language === 'hi' ? 'सहेजने में त्रुटि' : 'Save Error'}: ${detail}`);
    }
  };

  const handleExport = () => {
    if (!selectedName) return;
    window.open(`/protocols/${selectedName}/export`, '_blank');
  };

  const handleImportClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const resp = await axios.post('/protocols/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      showStatus('success', language === 'hi' ? 'प्रोटोकॉल आयातित किया गया' : `Protocol '${resp.data.name}' imported successfully`);
      fetchProtocols();
    } catch (err: any) {
      showStatus('error', language === 'hi' ? 'आयात विफल रहा' : 'Import failed: Invalid JSON file');
    } finally {
      if (e.target) e.target.value = '';
    }
  };

  const handleDelete = async () => {
    if (!selectedName) return;
    if (selectedName === 'interview_default') {
      showStatus('error', language === 'hi' ? 'डिफ़ॉल्ट प्रोटोकॉल हटाया नहीं जा सकता' : 'Cannot delete standard default protocol');
      return;
    }

    if (!window.confirm(`Delete protocol '${selectedName}'?`)) return;

    try {
      await axios.delete(`/protocols/${selectedName}`);
      showStatus('success', language === 'hi' ? 'प्रोटोकॉल हटाया गया' : `Protocol '${selectedName}' deleted`);
      fetchProtocols();
    } catch (err: any) {
      showStatus('error', language === 'hi' ? 'हटाने में त्रुटि' : 'Delete failed');
    }
  };

  const handleCreateNew = () => {
    const newProto = {
      name: `protocol_${Math.random().toString(36).substring(2, 7)}`,
      title: "Custom Academic Interview Protocol",
      languages: ["en", "hi"],
      steps: [
        { id: "intro", type: "scenario", question_en: "What subject are you studying?", question_hi: "आप किस विषय की पढ़ाई कर रहे हैं?" },
        { id: "strategy", type: "open_question", question_en: "Describe your primary study strategy.", question_hi: "अपनी मुख्य अध्ययन रणनीति का वर्णन करें।" },
        { id: "frequency", type: "likert_rating", min: 1, max: 5 },
        { id: "complete", type: "feedback_summary" }
      ]
    };
    setSelectedName(newProto.name);
    setJsonText(JSON.stringify(newProto, null, 2));
    showStatus('success', language === 'hi' ? 'नया प्रोटोकॉल ड्राफ्ट तैयार है' : 'New protocol template ready for editing');
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">
            {language === 'hi' ? 'साक्षात्कार प्रोटोकॉल एडिटर' : 'Interview Protocol Editor'}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {language === 'hi' ? 'साक्षात्कार के चरणों एवं प्रश्नों का अनुकूलन (JSON Schema API)' : 'Customize interview steps, scenarios, and prompts (CRUD & Export/Import)'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleCreateNew}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-medium text-xs transition border border-slate-700"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{language === 'hi' ? 'नया बनाएँ' : 'New Protocol'}</span>
          </button>

          <button
            onClick={handleImportClick}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-medium text-xs transition border border-slate-700"
          >
            <Upload className="w-3.5 h-3.5 text-indigo-400" />
            <span>{language === 'hi' ? 'आयात (Import)' : 'Import JSON'}</span>
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".json"
            className="hidden"
          />

          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-medium text-xs transition border border-slate-700"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span>{language === 'hi' ? 'निर्यात (Export)' : 'Export JSON'}</span>
          </button>

          {selectedName !== 'interview_default' && (
            <button
              onClick={handleDelete}
              className="flex items-center gap-1.5 px-3 py-2 bg-rose-900/40 hover:bg-rose-900/60 text-rose-300 rounded-xl font-medium text-xs transition border border-rose-800"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{language === 'hi' ? 'हटाएँ' : 'Delete'}</span>
            </button>
          )}

          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium shadow-lg transition text-sm shadow-indigo-600/30"
          >
            <Save className="w-4 h-4" />
            <span>{language === 'hi' ? 'सहेजें' : 'Save Protocol'}</span>
          </button>
        </div>
      </div>

      {/* Status Alert Banner */}
      {statusMessage && (
        <div className={`p-4 rounded-xl flex items-center gap-3 text-sm font-medium border ${
          statusMessage.type === 'success'
            ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
            : 'bg-rose-950/60 border-rose-500/40 text-rose-300'
        }`}>
          {statusMessage.type === 'success' ? <CheckCircle className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Protocol Selector & Schema Code Editor */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {language === 'hi' ? 'प्रोटोकॉल चुनें:' : 'Select Protocol:'}
            </span>
            <select
              value={selectedName}
              onChange={(e) => handleSelectProtocol(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-indigo-300 rounded-lg px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {protocols.map(p => (
                <option key={p.name} value={p.name}>
                  {p.title} ({p.name})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={fetchProtocols}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{language === 'hi' ? 'रीफ्रेश' : 'Reload'}</span>
          </button>
        </div>

        <textarea
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          rows={18}
          className="w-full bg-slate-950 font-mono text-sm text-indigo-300 p-4 rounded-xl border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 leading-relaxed shadow-inner"
        />
      </div>
    </div>
  );
};
