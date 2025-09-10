export interface User {
  id: number;
  username: string;
  age?: number; // Optional age field
  ai_character_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

export interface Conversation {
  id: number;
  message: string;
  response: string;
  language: string;
  created_at: string;
}

export interface DiaryEntry {
  id: number;
  content: string;
  answers: Record<string, any>;
  language: string;
  tone: string;
  created_at: string;
}

export interface GuidedDiarySession {
  id: number;
  language: string;
  current_phase: string;
  current_intent: string;
  structured_data: Record<string, any>;
  composed_diary?: string;
  final_diary?: string;
  is_complete: boolean;
  is_crisis: boolean;
  created_at: string;
  completed_at?: string;
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  intent?: string;
  slot_updates?: Record<string, any>;
  created_at: string;
}

export interface GuidedDiaryResponse {
  success: boolean;
  response: string;
  is_complete: boolean;
  is_crisis: boolean;
  current_phase: string;
  current_intent: string;
  structured_data: Record<string, any>;
  composed_diary?: string;
  final_diary?: string;
}