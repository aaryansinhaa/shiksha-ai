import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Database, MousePointer, Cpu, Users, Eye, MessageSquare, ChevronRight } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

interface StudentData {
  user_id: string;
  client: string;
  language: string;
  study_subject: string;
  completed: boolean;
  total_turns: number;
  completed_contexts_count?: number;
  transcript: { role: string; text: string; turn: number }[];
}

interface TelemetryData {
  mouse_traces: { id: number; user_id: string; session_id: string; x: number; y: number; timestamp: number }[];
  activity_logs: { id: string; user_id: string; action: string; value: any; timestamp: number }[];
}

export const ResearcherDashboard: React.FC = () => {
  const { language } = useChatStore();
  const [students, setStudents] = useState<StudentData[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryData>({ mouse_traces: [], activity_logs: [] });
  const [selectedStudent, setSelectedStudent] = useState<StudentData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sResp, tResp] = await Promise.all([
        axios.get('/researcher/students'),
        axios.get('/researcher/telemetry')
      ]);
      if (sResp.data) setStudents(sResp.data);
      if (tResp.data) setTelemetry(tResp.data);
    } catch (err) {
      console.error('Error loading researcher telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            {language === 'hi' ? 'अनुसंधान एवं टेलीमेट्री विश्लेषण' : 'Research Analytics & Telemetry Inspector'}
          </h2>
          <p className="text-sm text-slate-400">
            {language === 'hi'
              ? 'छात्र संवाद ट्रांसक्रिप्ट, माउस ट्रेसेस एवं RAG वेक्टर डेटाबेस'
              : 'Saved student records, raw conversation transcripts, and 100ms sampled mouse telemetry'}
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 transition"
        >
          {language === 'hi' ? 'डेटा रीफ्रेश करें' : 'Refresh Telemetry Data'}
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium">{language === 'hi' ? 'कुल रिकॉर्डेड छात्र' : 'Total Saved Students'}</p>
            <h3 className="text-2xl font-bold text-white mt-1">{students.length}</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 text-blue-400 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium">{language === 'hi' ? 'माउस ट्रेस पॉइंट' : 'Captured Mouse Traces'}</p>
            <h3 className="text-2xl font-bold text-purple-400 mt-1">{telemetry.mouse_traces.length} pts</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-600/20 text-purple-400 flex items-center justify-center">
            <MousePointer className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium">{language === 'hi' ? 'वेक्टर मॉडल' : 'Vector Architecture'}</p>
            <h3 className="text-sm font-bold text-emerald-400 mt-1">pgvector (768-dim)</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-600/20 text-emerald-400 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Saved Students Information Roster */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          {language === 'hi' ? 'सभी छात्रों की सहेजी गई जानकारी (Student Roster & Transcripts)' : 'Saved Student Records & Full Transcripts'}
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[11px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">User ID</th>
                <th className="py-3 px-4">Subject</th>
                <th className="py-3 px-4">Language</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Scenarios</th>
                <th className="py-3 px-4">Turns</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {students.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500">
                    No student records found. Complete an interview on the home page to populate data.
                  </td>
                </tr>
              ) : (
                students.map((std, i) => (
                  <tr key={i} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-mono text-xs text-indigo-300">{std.user_id}</td>
                    <td className="py-3 px-4 font-medium text-white">{std.study_subject}</td>
                    <td className="py-3 px-4 uppercase text-xs font-semibold">{std.language}</td>
                    <td className="py-3 px-4">
                      {std.completed ? (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          Completed
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          In Progress
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-indigo-300">
                      {std.completed_contexts_count !== undefined ? std.completed_contexts_count : (std.completed ? 6 : 1)} / 6
                    </td>
                    <td className="py-3 px-4 font-mono">{std.total_turns}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedStudent(std)}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600 text-indigo-200 text-xs font-medium border border-indigo-500/30 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Transcript
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live Telemetry Mouse Trace Log Stream */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <MousePointer className="w-5 h-5 text-purple-400" />
          {language === 'hi' ? 'लाइव माउस ट्रेसेस लॉग (100ms सैंपल)' : 'Live Mouse Telemetry Trace Log Stream (PostgreSQL)'}
        </h3>

        <div className="max-h-64 overflow-y-auto border border-slate-800 rounded-xl bg-slate-950 p-4 font-mono text-xs text-slate-400 space-y-2">
          {telemetry.mouse_traces.length === 0 ? (
            <p className="text-slate-500 text-center py-4">No mouse telemetry data logged yet. Move your mouse across the app to stream logs.</p>
          ) : (
            telemetry.mouse_traces.map((mt, i) => (
              <div key={i} className="flex items-center justify-between border-b border-slate-900 pb-1">
                <span className="text-purple-400">Trace #{mt.id}</span>
                <span className="text-slate-300">User: {mt.user_id || 'Anonymous'}</span>
                <span className="text-emerald-400">Coordinates: ({mt.x}, {mt.y})</span>
                <span className="text-slate-500">{new Date(mt.timestamp).toLocaleTimeString()}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Student Transcript Modal */}
      {selectedStudent && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel max-w-2xl w-full max-h-[80vh] flex flex-col rounded-3xl border border-slate-800 bg-slate-950 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-indigo-400" />
                  Transcript for {selectedStudent.user_id}
                </h3>
                <p className="text-xs text-slate-400">Subject: {selectedStudent.study_subject} | Language: {selectedStudent.language}</p>
              </div>
              <button
                onClick={() => setSelectedStudent(null)}
                className="text-slate-400 hover:text-white text-sm font-semibold px-3 py-1 rounded-lg bg-slate-800"
              >
                Close
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 p-2">
              {selectedStudent.transcript.map((msg, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-2xl text-xs leading-relaxed max-w-[85%] ${
                    msg.role === 'user'
                      ? 'ml-auto bg-indigo-600 text-white rounded-br-none'
                      : 'bg-slate-900 text-slate-200 border border-slate-800 rounded-bl-none'
                  }`}
                >
                  <p className="font-semibold text-[10px] opacity-70 mb-1">
                    {msg.role === 'user' ? 'Student' : 'Shiksha AI Advisor'} (Turn {msg.turn})
                  </p>
                  <p>{msg.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
