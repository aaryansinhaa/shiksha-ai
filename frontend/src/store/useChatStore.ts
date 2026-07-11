import { create } from 'zustand';

export interface ChatMessage {
  id: number;
  author: 'user' | 'bot';
  message: string;
}

interface ChatState {
  userId: string;
  client: string;
  language: 'en' | 'hi';
  messages: ChatMessage[];
  isInterviewComplete: boolean;
  isLoading: boolean;
  hasConsent: boolean;
  currentStep: string;
  currentContext: number;
  totalContexts: number;
  completedCount: number;
  
  setLanguage: (lang: 'en' | 'hi') => void;
  setHasConsent: (consent: boolean) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  addMessage: (msg: ChatMessage) => void;
  setIsInterviewComplete: (complete: boolean) => void;
  setIsLoading: (loading: boolean) => void;
  setContextProgress: (current: number, total: number, completed?: number) => void;
  resetSession: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  userId: `user_${Math.random().toString(36).substring(2, 9)}`,
  client: 'web',
  language: 'en',
  messages: [],
  isInterviewComplete: false,
  isLoading: false,
  hasConsent: false,
  currentStep: 'intro',
  currentContext: 1,
  totalContexts: 6,
  completedCount: 0,

  setLanguage: (lang) => set({ language: lang }),
  setHasConsent: (consent) => set({ hasConsent: consent }),
  setMessages: (msgs) => set({ messages: msgs }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setIsInterviewComplete: (complete) => set({ isInterviewComplete: complete }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setContextProgress: (current, total, completed) => set((state) => ({
    currentContext: current || state.currentContext,
    totalContexts: total || state.totalContexts,
    completedCount: completed !== undefined ? completed : state.completedCount
  })),
  resetSession: () => set({
    userId: `user_${Math.random().toString(36).substring(2, 9)}`,
    messages: [],
    isInterviewComplete: false,
    currentStep: 'intro',
    currentContext: 1,
    totalContexts: 6,
    completedCount: 0
  })
}));
