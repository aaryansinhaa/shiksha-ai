import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Users, CheckCircle2, Award, TrendingUp } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const TeacherDashboard: React.FC = () => {
  const { language } = useChatStore();
  const [stats, setStats] = useState({
    total_users: 1,
    completed_interviews: 1,
    strategy_distribution: {
      '008-001 (Rehearsal)': 12,
      '002-001 (Organizing)': 8,
      '003-001 (Goal Setting)': 15,
      '006-001 (Environment)': 6,
      '009-001 (Social Help)': 9
    },
    average_turns: 4.5
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const resp = await axios.get('/dashboard/stats');
      if (resp.data) setStats(resp.data);
    } catch (err) {
      // Use fallback stats for demo
    }
  };

  const chartData = Object.entries(stats.strategy_distribution).map(([key, val]) => ({
    name: key,
    count: val
  }));

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">
          {language === 'hi' ? 'शिक्षक डैशबोर्ड एवं शिक्षण रणनीति विश्लेषण' : 'Teacher Dashboard & Strategy Analytics'}
        </h2>
        <p className="text-sm text-slate-400">
          {language === 'hi' ? 'छात्रों की स्व-नियमित सीखने (SRL) की रणनीतियों का कुल विश्लेषण' : 'Cohort-wide Self-Regulated Learning (SRL) strategy distribution metrics'}
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium">{language === 'hi' ? 'कुल छात्र' : 'Total Students'}</p>
            <h3 className="text-2xl font-bold text-white mt-1">{stats.total_users}</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 text-blue-400 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium">{language === 'hi' ? 'पूर्ण साक्षात्कार' : 'Completed Interviews'}</p>
            <h3 className="text-2xl font-bold text-emerald-400 mt-1">{stats.completed_interviews}</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-600/20 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium">{language === 'hi' ? 'औसत संवाद टर्न' : 'Avg. Turns / Interview'}</p>
            <h3 className="text-2xl font-bold text-indigo-400 mt-1">{stats.average_turns}</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium">{language === 'hi' ? 'शीर्ष रणनीति' : 'Top Strategy'}</p>
            <h3 className="text-lg font-bold text-amber-400 mt-1">Goal Setting</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-600/20 text-amber-400 flex items-center justify-center">
            <Award className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Strategy Distribution Recharts */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-semibold text-white mb-4">
          {language === 'hi' ? 'अध्ययन रणनीति वितरण (Zimmerman Model)' : 'Strategy Usage Frequency Distribution'}
        </h3>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#fff' }}
              />
              <Bar dataKey="count" fill="#4f46e5" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
