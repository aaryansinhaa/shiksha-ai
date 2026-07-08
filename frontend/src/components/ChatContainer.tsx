import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Bot, User as UserIcon, RefreshCw, Star, Sparkles } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';
import { ResultsView } from './ResultsView';

export const ChatContainer: React.FC = () => {
  const {
    userId, client, language, messages, addMessage, setMessages,
    isInterviewComplete, setIsInterviewComplete, isLoading, setIsLoading, resetSession
  } = useChatStore();

  const [input, setInput] = useState('');
  const [showLikert, setShowLikert] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Initialize conversation on start
  useEffect(() => {
    if (messages.length === 0) {
      initConversation();
    }
  }, [language]);

  const initConversation = async () => {
    setIsLoading(true);
    try {
      const resp = await axios.post('/startConversation', {
        userid: userId,
        client: client,
        language: language
      });
      setMessages([{ id: 1, author: 'bot', message: resp.data.message }]);
    } catch (err) {
      setMessages([{
        id: 1,
        author: 'bot',
        message: language === 'hi'
          ? 'नमस्ते! शिक्षा AI साक्षात्कार में आपका स्वागत है। आप किस विषय की पढ़ाई कर रहे हैं?'
          : 'Hello! Welcome to Shiksha AI interview. What subject are you studying?'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (textToSend?: string) => {
    const messageContent = textToSend || input;
    if (!messageContent.trim() || isLoading) return;

    const newMsgId = messages.length + 1;
    addMessage({ id: newMsgId, author: 'user', message: messageContent });
    if (!textToSend) setInput('');
    setIsLoading(true);

    try {
      const resp = await axios.post('/reply', {
        userid: userId,
        client: client,
        message: messageContent
      });

      addMessage({ id: newMsgId + 1, author: 'bot', message: resp.data.message });
      if (resp.data.complete) {
        setIsInterviewComplete(true);
      }

      // Show Likert rating selector if bot asks for frequency rating
      if (resp.data.message.includes('1 से 5') || resp.data.message.includes('1 to 5')) {
        setShowLikert(true);
      } else {
        setShowLikert(false);
      }

    } catch (err) {
      addMessage({
        id: newMsgId + 1,
        author: 'bot',
        message: language === 'hi'
          ? 'क्षमा करें, संदेश संसाधित करने में समस्या आई। कृपया पुनः प्रयास करें।'
          : 'Sorry, failed to process response. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isInterviewComplete) {
    return <ResultsView />;
  }

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] max-w-4xl mx-auto p-4">
      {/* Header Info */}
      <div className="flex items-center justify-between glass-card p-4 rounded-2xl mb-4 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Shiksha AI Study Advisor</h3>
            <p className="text-xs text-indigo-400">
              {language === 'hi' ? 'द्विभाषी (हिन्दी/अंग्रेज़ी) GenAI साक्षात्कार' : 'Bilingual (Hindi/English) GenAI Interview'}
            </p>
          </div>
        </div>

        <button
          onClick={resetSession}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>{language === 'hi' ? 'नया सत्र' : 'Reset Session'}</span>
        </button>
      </div>

      {/* Message History List */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${msg.author === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
              msg.author === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-indigo-400 border border-slate-700'
            }`}>
              {msg.author === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className={`max-w-xl p-4 rounded-2xl text-sm leading-relaxed ${
              msg.author === 'user'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-500/10'
                : 'glass-card text-slate-200 rounded-tl-none border border-slate-800'
            }`}>
              {msg.message}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-800 text-indigo-400 border border-slate-700 flex items-center justify-center">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="glass-card px-4 py-3 rounded-2xl rounded-tl-none text-xs text-slate-400 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
              <span>{language === 'hi' ? 'उत्तर तैयार हो रहा है...' : 'Generating AI response...'}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Likert Frequency Rating Bar */}
      {showLikert && !isInterviewComplete && (
        <div className="glass-card p-3 rounded-xl mb-3 border border-indigo-500/30 flex items-center justify-between">
          <span className="text-xs text-indigo-300 font-medium flex items-center gap-1.5">
            <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
            {language === 'hi' ? 'आवृति चुनें (Likert 1-5):' : 'Select Frequency Rating (1-5):'}
          </span>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((val) => (
              <button
                key={val}
                onClick={() => handleSend(val.toString())}
                className="w-8 h-8 rounded-lg bg-indigo-600/30 hover:bg-indigo-600 text-indigo-200 hover:text-white text-xs font-bold transition-all border border-indigo-500/40"
              >
                {val}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="mt-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading || isInterviewComplete}
            placeholder={
              isInterviewComplete
                ? (language === 'hi' ? 'साक्षात्कार पूर्ण हो गया है।' : 'Interview completed.')
                : (language === 'hi' ? 'अपनी अध्ययन विधि यहाँ लिखें...' : 'Describe your study approach here...')
            }
            className="flex-1 px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-slate-100 placeholder-slate-500 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={isLoading || !input.trim() || isInterviewComplete}
            className="px-5 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
