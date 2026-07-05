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
  
  setLanguage: (lang: 'en' | 'hi') => void;
  setHasConsent: (consent: boolean) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  addMessage: (msg: ChatMessage) => void;
  setIsInterviewComplete: (complete: boolean) => void;
  setIsLoading: (loading: boolean) => void;
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

  setLanguage: (lang) => set({ language: lang }),
  setHasConsent: (consent) => set({ hasConsent: consent }),
  setMessages: (msgs) => set({ messages: msgs }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setIsInterviewComplete: (complete) => set({ isInterviewComplete: complete }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  resetSession: () => set({
    userId: `user_${Math.random().toString(36).substring(2, 9)}`,
    messages: [],
    isInterviewComplete: false,
    currentStep: 'intro'
  })
}));
