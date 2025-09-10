import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthResponse } from '../types/index.ts';
import { authAPI } from '../utils/api.ts';

interface AuthContextType {
  user: User | null;
  token: string | null;
  language: string;
  setLanguage: (language: string) => void;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, age: number | null, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  updateCharacterName: (characterName: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [language, setLanguageState] = useState<string>('en');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      const savedLanguage = localStorage.getItem('language');

      // Initialize language from localStorage or default to 'en'
      if (savedLanguage) {
        setLanguageState(savedLanguage);
      }

      if (savedToken && savedUser) {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        
        // Verify token is still valid
        try {
          const userData = await authAPI.getMe();
          setUser(userData);
        } catch (error) {
          // Token is invalid, clear storage
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response: AuthResponse = await authAPI.login(username, password);
      
      setToken(response.access_token);
      setUser(response.user);
      
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
    } catch (error) {
      throw error;
    }
  };

  const register = async (username: string, age: number | null, password: string) => {
    try {
      const response: AuthResponse = await authAPI.register(username, age, password);
      
      setToken(response.access_token);
      setUser(response.user);
      
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    // Keep language preference on logout
  };

  const setLanguage = (newLanguage: string) => {
    setLanguageState(newLanguage);
    localStorage.setItem('language', newLanguage);
  };

  const updateCharacterName = async (characterName: string) => {
    try {
      await authAPI.updateCharacterName(characterName);
      if (user) {
        const updatedUser = { ...user, ai_character_name: characterName };
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }
    } catch (error) {
      throw error;
    }
  };

  const value = {
    user,
    token,
    language,
    setLanguage,
    login,
    register,
    logout,
    loading,
    updateCharacterName,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};