import axios from 'axios';
import { AuthResponse, User, Conversation, DiaryEntry } from '../types';

// Auto-detect API host from browser hostname for mobile support
const hostname = window.location.hostname;
const API_BASE_URL = (hostname === 'localhost' || hostname === '127.0.0.1')
  ? 'http://localhost:8001'
  : `http://${hostname}:8001`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: async (username: string, age: number | null, password: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', { username, age, password });
    return response.data;
  },

  login: async (username: string, password: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateCharacterName: async (characterName: string): Promise<{ message: string; character_name: string }> => {
    const response = await api.put('/auth/character-name', { character_name: characterName });
    return response.data;
  },
};

export const llmAPI = {
  getModels: async (language: string) => {
    const response = await api.get(`/llm/models/${language}`);
    return response.data;
  },

  sendMessage: async (
    message: string,
    conversationHistory: any[] = [],
    language: string = 'en'
  ) => {
    const response = await api.post('/llm/conversation', {
      message,
      conversation_history: conversationHistory,
      language,
    });
    return response.data;
  },
};

export const diaryAPI = {
  generate: async (
    answers: Record<string, any>,
    conversationHistory: any[] = [],
    language: string = 'en',
    tone: string = 'reflective'
  ) => {
    const response = await api.post('/diary/generate', {
      answers,
      conversation_history: conversationHistory,
      language,
      tone,
    });
    return response.data;
  },

  getEntries: async (): Promise<{ success: boolean; entries: DiaryEntry[] }> => {
    const response = await api.get('/diary/entries');
    return response.data;
  },

  getDates: async (): Promise<{ success: boolean; dates: string[] }> => {
    const response = await api.get('/diary/dates');
    return response.data;
  },

  getByDate: async (date: string): Promise<{ success: boolean; entries: DiaryEntry[]; date: string }> => {
    const response = await api.get(`/diary/by-date/${date}`);
    return response.data;
  },

  editEntry: async (entryId: number, content: string): Promise<{ success: boolean; entry: DiaryEntry }> => {
    const response = await api.put(`/diary/entry/${entryId}`, { content });
    return response.data;
  },

  deleteEntry: async (entryId: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/diary/entry/${entryId}`);
    return response.data;
  },

  getConversation: async (entryId: number): Promise<{ success: boolean; conversation_history: any[]; entry_id: number; created_at: string }> => {
    const response = await api.get(`/diary/entry/${entryId}/conversation`);
    return response.data;
  },
};

export const guidedDiaryAPI = {
  startSession: async (language: string = 'en') => {
    const response = await api.post('/guided-diary/start', { language });
    return response.data;
  },

  sendMessage: async (sessionId: number, message: string, language: string = 'en') => {
    const response = await api.post(`/guided-diary/${sessionId}/message`, { message, language });
    return response.data;
  },

  getSession: async (sessionId: number) => {
    const response = await api.get(`/guided-diary/${sessionId}`);
    return response.data;
  },

  editDiary: async (sessionId: number, editedContent: string) => {
    const response = await api.post(`/guided-diary/${sessionId}/edit`, { edited_content: editedContent });
    return response.data;
  },

  getActiveSession: async () => {
    const response = await api.get('/guided-diary-session/active');
    return response.data;
  },

  getDates: async (): Promise<{ success: boolean; dates: string[] }> => {
    const response = await api.get('/guided-diary-calendar/dates');
    return response.data;
  },

  getByDate: async (date: string) => {
    const response = await api.get(`/guided-diary-calendar/by-date/${date}`);
    return response.data;
  },

  editSessionDiary: async (sessionId: number, finalDiary: string): Promise<{ success: boolean; session: any }> => {
    const response = await api.put(`/guided-diary/session/${sessionId}/final-diary`, { final_diary: finalDiary });
    return response.data;
  },

  deleteSession: async (sessionId: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/guided-diary/${sessionId}/delete`);
    return response.data;
  },
};

export const conversationAPI = {
  getHistory: async (): Promise<{ success: boolean; conversations: Conversation[] }> => {
    const response = await api.get('/conversations');
    return response.data;
  },
};

export const unifiedDiaryAPI = {
  getDates: async (): Promise<{ success: boolean; dates: string[] }> => {
    const response = await api.get('/unified-diary/dates');
    return response.data;
  },

  getByDate: async (date: string): Promise<{ success: boolean; entries: any[]; date: string }> => {
    const response = await api.get(`/unified-diary/by-date/${date}`);
    return response.data;
  },
};

export const freeEntryAPI = {
  correctGrammar: async (text: string, language: string = 'en'): Promise<{ success: boolean; original_text: string; corrected_text: string }> => {
    const response = await api.post('/free-entry/correct-grammar', { text, language });
    return response.data;
  },

  improveWriting: async (
    text: string, 
    language: string = 'en', 
    improvementType: string = 'general'
  ): Promise<{ success: boolean; original_text: string; improved_text: string; improvement_type: string }> => {
    const response = await api.post('/free-entry/improve-writing', { 
      text, 
      language, 
      improvement_type: improvementType
    });
    return response.data;
  },

  save: async (
    originalText: string,
    finalText: string,
    language: string = 'en'
  ): Promise<{ success: boolean; entry_id: number; message: string }> => {
    const response = await api.post('/free-entry/save', { 
      original_text: originalText, 
      final_text: finalText, 
      language 
    });
    return response.data;
  },
};

export default api;