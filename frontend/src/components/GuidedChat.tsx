import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import { guidedDiaryAPI, diaryAPI, unifiedDiaryAPI } from '../utils/api.ts';
import { GuidedDiarySession, ConversationMessage, GuidedDiaryResponse } from '../types/index.ts';
import SimpleCalendar from './SimpleCalendar.tsx';

interface GuidedChatProps {
  onSwitchToLegacy: () => void;
}

const GuidedChat: React.FC<GuidedChatProps> = ({ onSwitchToLegacy }) => {
  const [session, setSession] = useState<GuidedDiarySession | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [isEditingDiary, setIsEditingDiary] = useState(false);
  const [editedDiary, setEditedDiary] = useState('');
  const [selectedDateSessions, setSelectedDateSessions] = useState<any[]>([]);
  const [showHistoricalDiary, setShowHistoricalDiary] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedModel, setSelectedModel] = useState('llama3.1:8b');
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load active session on component mount
    loadActiveSession();
  }, []);

  const loadActiveSession = async () => {
    try {
      setLoading(true);
      const response = await guidedDiaryAPI.getActiveSession();
      if (response.success && response.session) {
        // Check if the session is from today
        const sessionDate = new Date(response.session.created_at).toDateString();
        const today = new Date().toDateString();
        
        if (sessionDate === today && !response.session.is_complete) {
          // Only load if it's from today and not complete
          setSession(response.session);
          setMessages(response.conversation_history || []);
          setLanguage(response.session.language);
          if (response.session.final_diary) {
            setEditedDiary(response.session.final_diary);
          }
        } else {
          // Start fresh if session is old or complete
          startNewSession();
        }
      } else {
        // No active session, start fresh
        startNewSession();
      }
    } catch (error) {
      console.error('Error loading active session:', error);
      // If error, start fresh
      startNewSession();
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = async () => {
    try {
      // Clear all state immediately before any async operations
      setSession(null);
      setMessages([]);
      setEditedDiary('');
      setIsEditingDiary(false);
      setInputMessage('');
      
      // Force a small delay to ensure UI clears
      await new Promise(resolve => setTimeout(resolve, 100));
      
      setLoading(true);
      
      const response = await guidedDiaryAPI.startSession(language, selectedModel);
      if (response.success) {
        const newSession: GuidedDiarySession = {
          id: response.session_id,
          language: response.language,
          current_phase: 'guide',
          current_intent: response.current_intent,
          structured_data: {},
          is_complete: false,
          is_crisis: false,
          created_at: new Date().toISOString()
        };
        setSession(newSession);
        
        // Add initial message
        const initialMessage: ConversationMessage = {
          role: 'assistant',
          content: response.initial_message,
          created_at: new Date().toISOString()
        };
        setMessages([initialMessage]);
      }
    } catch (error) {
      console.error('Error starting session:', error);
      // Reset to clean state on error
      setSession(null);
      setMessages([]);
      setEditedDiary('');
      setIsEditingDiary(false);
      setInputMessage('');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading || !session) return;

    const userMessage: ConversationMessage = {
      role: 'user',
      content: inputMessage,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response: GuidedDiaryResponse = await guidedDiaryAPI.sendMessage(
        session.id,
        inputMessage,
        language,
        selectedModel
      );

      if (response.success) {
        const assistantMessage: ConversationMessage = {
          role: 'assistant',
          content: response.response,
          created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, assistantMessage]);

        // Update session data
        setSession(prev => prev ? {
          ...prev,
          current_phase: response.current_phase,
          current_intent: response.current_intent,
          structured_data: response.structured_data,
          composed_diary: response.composed_diary,
          final_diary: response.final_diary,
          is_complete: response.is_complete,
          is_crisis: response.is_crisis
        } : null);

        // If diary is complete, set up editing
        if (response.is_complete && response.final_diary) {
          setEditedDiary(response.final_diary);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ConversationMessage = {
        role: 'assistant',
        content: language === 'en' 
          ? 'Sorry, something went wrong. Please try again.'
          : '抱歉，出现了一些问题。请再试一次。',
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const startEditing = () => {
    setIsEditingDiary(true);
  };

  const cancelEditing = () => {
    setIsEditingDiary(false);
    if (session?.final_diary) {
      setEditedDiary(session.final_diary);
    }
  };

  const saveDiaryEdit = async () => {
    if (!session) return;
    
    try {
      setLoading(true);
      await guidedDiaryAPI.editDiary(session.id, editedDiary);
      setSession(prev => prev ? { ...prev, final_diary: editedDiary } : null);
      setIsEditingDiary(false);
    } catch (error) {
      console.error('Error saving diary edit:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDateSelect = async (date: string, sessions: any[]) => {
    setSelectedDate(date);
    setSelectedDateSessions(sessions);
    setShowHistoricalDiary(true);
    setEditingEntryId(null); // Reset editing state
    setEditingContent('');
  };

  const startEditingEntry = (entryId: string, content: string) => {
    setEditingEntryId(entryId);
    setEditingContent(content);
  };

  const cancelEditingEntry = () => {
    setEditingEntryId(null);
    setEditingContent('');
  };

  const saveEntryEdit = async (entryId: string, mode: string) => {
    try {
      setLoading(true);
      
      if (mode === 'casual') {
        const numericId = parseInt(entryId.replace('casual_', ''));
        await diaryAPI.editEntry(numericId, editingContent);
      } else if (mode === 'guided') {
        const numericId = parseInt(entryId.replace('guided_', ''));
        await guidedDiaryAPI.editSessionDiary(numericId, editingContent);
      }
      
      // Update local state
      setSelectedDateSessions(prev => 
        prev.map(entry => 
          entry.id === entryId 
            ? { ...entry, content: editingContent }
            : entry
        )
      );
      
      setEditingEntryId(null);
      setEditingContent('');
    } catch (error) {
      console.error('Error saving entry edit:', error);
      alert(language === 'en' ? 'Failed to save changes' : '保存失败');
    } finally {
      setLoading(false);
    }
  };

  const deleteEntry = async (entryId: string, mode: string) => {
    const confirmMessage = language === 'en' 
      ? 'Are you sure you want to delete this diary entry? This action cannot be undone.'
      : '确定要删除这个日记条目吗？此操作无法撤销。';
    
    if (!window.confirm(confirmMessage)) return;
    
    try {
      setLoading(true);
      
      if (mode === 'casual') {
        const numericId = parseInt(entryId.replace('casual_', ''));
        await diaryAPI.deleteEntry(numericId);
      } else if (mode === 'guided') {
        const numericId = parseInt(entryId.replace('guided_', ''));
        await guidedDiaryAPI.deleteSession(numericId);
      }
      
      // Remove from local state
      setSelectedDateSessions(prev => 
        prev.filter(entry => entry.id !== entryId)
      );
      
      // If no entries left, close modal
      if (selectedDateSessions.length <= 1) {
        setShowHistoricalDiary(false);
      }
    } catch (error) {
      console.error('Error deleting entry:', error);
      alert(language === 'en' ? 'Failed to delete entry' : '删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getPhaseTitle = () => {
    if (!session) return '';
    
    if (session.is_crisis) {
      return language === 'en' ? 'Crisis Support' : '危机支持';
    }
    
    switch (session.current_phase) {
      case 'guide':
        return language === 'en' ? 'Daily Reflection' : '每日反思';
      case 'compose':
        return language === 'en' ? 'Creating Your Diary' : '创建你的日记';
      case 'complete':
        return language === 'en' ? 'Diary Complete' : '日记完成';
      default:
        return language === 'en' ? 'Guided Diary' : '引导式日记';
    }
  };

  const getIntentDescription = () => {
    if (!session) return '';
    
    const descriptions = {
      en: {
        'ASK_MOOD': 'Exploring how you feel',
        'ASK_ACTIVITIES': 'Learning about your day',
        'ASK_CHALLENGES_WINS': 'Discussing challenges and wins',
        'ASK_GRATITUDE': 'Finding gratitude',
        'ASK_HOPE': 'Looking ahead with hope',
        'ASK_EXTRA': 'Any final thoughts',
        'COMPOSE': 'Writing your diary',
        'COMPLETE': 'Ready for review'
      },
      zh: {
        'ASK_MOOD': '探索你的感受',
        'ASK_ACTIVITIES': '了解你的一天',
        'ASK_CHALLENGES_WINS': '讨论挑战和收获',
        'ASK_GRATITUDE': '寻找感恩',
        'ASK_HOPE': '怀着希望展望未来',
        'ASK_EXTRA': '最后的想法',
        'COMPOSE': '写你的日记',
        'COMPLETE': '准备回顾'
      }
    };
    
    return descriptions[language as 'en' | 'zh'][session.current_intent] || '';
  };

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Left Sidebar - Calendar */}
      <div style={{ 
        width: '300px', 
        backgroundColor: 'white', 
        borderRight: '1px solid #e0e0e0',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ marginBottom: '10px', color: '#333' }}>Welcome, {user?.username}!</h3>
          <p style={{ color: '#666', fontSize: '14px' }}>{user?.email}</p>
          <button
            onClick={logout}
            style={{
              marginTop: '10px',
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Logout
          </button>
          {onSwitchToLegacy && (
            <button
              onClick={onSwitchToLegacy}
              style={{
                marginTop: '10px',
                marginLeft: '10px',
                padding: '8px 16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              {language === 'en' ? 'Try Casual Mode' : '尝试休闲模式'}
            </button>
          )}
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
            Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #e0e0e0',
              borderRadius: '5px',
            }}
          >
            <option value="en">English</option>
            <option value="zh">中文</option>
          </select>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
            AI Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #e0e0e0',
              borderRadius: '5px',
            }}
          >
            <option value="llama3.1:8b">Llama 3.1 (8B)</option>
            <option value="qwen3:8b">Qwen 3 (8B)</option>
          </select>
        </div>

        <SimpleCalendar 
          language={language}
          onDateSelect={handleDateSelect}
        />

        <button
          onClick={startNewSession}
          disabled={loading}
          style={{
            width: '100%',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            padding: '12px',
            borderRadius: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.5 : 1,
            marginTop: '20px'
          }}
        >
          ✨ {language === 'en' ? 'Start Fresh Session' : '开始新对话'}
        </button>
      </div>

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#f9f9f9' }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          backgroundColor: 'white',
          borderBottom: '1px solid #e0e0e0'
        }}>
          <h1 style={{ margin: 0, color: '#667eea', fontWeight: '300' }}>Dear Me</h1>
          <p style={{ margin: '2px 0 0 0', color: '#999', fontSize: '0.8rem', fontStyle: 'italic' }}>
            Be Here, Be Now, Be You -- in a space you call your own
          </p>
        </div>

        {/* Messages Area */}
        <div style={{
          flex: 1,
          padding: '20px',
          overflowY: 'auto'
        }}>
          {!session ? (
            <div style={{ textAlign: 'center', marginTop: '50px' }}>
              <h3 style={{ color: '#495057', marginBottom: '20px' }}>
                {language === 'en' ? 'Welcome to Guided Diary' : '欢迎使用引导式日记'}
              </h3>
              <p style={{ color: '#6c757d', marginBottom: '30px' }}>
                {language === 'en' 
                  ? 'Start a guided conversation that will help you reflect on your day and create a meaningful diary entry.'
                  : '开始一次引导对话，帮助你反思一天并创建有意义的日记条目。'}
              </p>
              <button
                onClick={startNewSession}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  cursor: 'pointer'
                }}
                disabled={loading}
              >
                {loading 
                  ? (language === 'en' ? 'Starting...' : '开始中...')
                  : (language === 'en' ? 'Start Today\'s Reflection' : '开始今天的反思')}
              </button>
            </div>
          ) : (
            <>
              {messages.map((message, index) => (
                <div
                  key={index}
                  style={{
                    marginBottom: '15px',
                    display: 'flex',
                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <div style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: '18px',
                    backgroundColor: message.role === 'user' ? '#667eea' : 'white',
                    color: message.role === 'user' ? 'white' : '#333',
                    border: message.role === 'assistant' ? '1px solid #e0e0e0' : 'none'
                  }}>
                    <p style={{ margin: 0, fontSize: '14px', textAlign: 'left' }}>{message.content}</p>
                    <p style={{ 
                      margin: '5px 0 0 0', 
                      fontSize: '12px', 
                      opacity: 0.7,
                      textAlign: 'left'
                    }}>
                      {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}

              {/* Show thinking indicator when loading */}
              {loading && (
                <div style={{
                  marginBottom: '15px',
                  display: 'flex',
                  justifyContent: 'flex-start'
                }}>
                  <div style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: '18px',
                    backgroundColor: 'white',
                    color: '#333',
                    border: '1px solid #e0e0e0'
                  }}>
                    <p style={{ margin: 0, fontSize: '14px', textAlign: 'left', fontStyle: 'italic' }}>
                      {language === 'en' ? 'Thinking...' : '思考中...'}
                    </p>
                  </div>
                </div>
              )}

              {/* Show diary when complete */}
              {session.is_complete && session.final_diary && (
                <div style={{ 
                  marginTop: '30px',
                  padding: '20px',
                  backgroundColor: 'white',
                  borderRadius: '10px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}>
                  <h4 style={{ color: '#495057', marginBottom: '15px' }}>
                    {language === 'en' ? 'Your Diary Entry' : '你的日记条目'}
                  </h4>
                  
                  {isEditingDiary ? (
                    <div>
                      <textarea
                        value={editedDiary}
                        onChange={(e) => setEditedDiary(e.target.value)}
                        style={{
                          width: '100%',
                          minHeight: '200px',
                          padding: '15px',
                          border: '2px solid #007bff',
                          borderRadius: '8px',
                          fontSize: '14px',
                          lineHeight: '1.6',
                          resize: 'vertical',
                          fontFamily: 'inherit',
                          outline: 'none',
                        }}
                        placeholder={language === 'en' ? 'Edit your diary...' : '编辑你的日记...'}
                      />
                      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                        <button
                          onClick={saveDiaryEdit}
                          disabled={loading}
                          style={{
                            padding: '8px 16px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          {loading ? (language === 'en' ? 'Saving...' : '保存中...') : (language === 'en' ? 'Save' : '保存')}
                        </button>
                        <button
                          onClick={cancelEditing}
                          style={{
                            padding: '8px 16px',
                            backgroundColor: '#6c757d',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          {language === 'en' ? 'Cancel' : '取消'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div style={{
                        padding: '15px',
                        backgroundColor: '#f8f9fa',
                        border: '1px solid #e9ecef',
                        borderRadius: '8px',
                        marginBottom: '15px',
                        whiteSpace: 'pre-wrap',
                        lineHeight: '1.6'
                      }}>
                        {session.final_diary}
                      </div>
                      <button
                        onClick={startEditing}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#007bff',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer'
                        }}
                      >
                        {language === 'en' ? 'Edit' : '编辑'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        {session && !session.is_complete && (
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            borderTop: '1px solid #e9ecef'
          }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={language === 'en' ? 'Type your message...' : '输入你的消息...'}
                disabled={loading}
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '25px',
                  fontSize: '16px',
                  outline: 'none'
                }}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !inputMessage.trim()}
                style={{
                  backgroundColor: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '50%',
                  width: '45px',
                  height: '45px',
                  cursor: 'pointer',
                  fontSize: '18px',
                  opacity: loading || !inputMessage.trim() ? 0.5 : 1
                }}
              >
                ➤
              </button>
            </div>
            
            {/* Generate Diary Button - shows when ready to compose */}
            {session.current_intent === 'ASK_EXTRA' && (
              <div style={{ marginTop: '15px', textAlign: 'center' }}>
                <button
                  onClick={async () => {
                    // Manually trigger diary generation by sending empty message to move to COMPOSE
                    if (!session) return;
                    
                    setLoading(true);
                    try {
                      const response = await guidedDiaryAPI.sendMessage(
                        session.id,
                        "I'm ready to generate my diary now.", // Trigger message
                        language,
                        selectedModel
                      );

                      if (response.success) {
                        const assistantMessage = {
                          role: 'assistant' as const,
                          content: response.response,
                          created_at: new Date().toISOString()
                        };

                        setMessages(prev => [...prev, assistantMessage]);

                        // Update session data
                        setSession(prev => prev ? {
                          ...prev,
                          current_phase: response.current_phase,
                          current_intent: response.current_intent,
                          structured_data: response.structured_data,
                          composed_diary: response.composed_diary,
                          final_diary: response.final_diary,
                          is_complete: response.is_complete,
                          is_crisis: response.is_crisis
                        } : null);

                        if (response.is_complete && response.final_diary) {
                          setEditedDiary(response.final_diary);
                        }
                      }
                    } catch (error) {
                      console.error('Error generating diary:', error);
                    } finally {
                      setLoading(false);
                    }
                  }}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '25px',
                    cursor: 'pointer',
                    fontSize: '16px',
                    fontWeight: 'bold'
                  }}
                  disabled={loading}
                >
                  {loading ? '...' : (language === 'en' ? '📝 Generate My Diary' : '📝 生成我的日记')}
                </button>
                <p style={{ 
                  margin: '8px 0 0 0', 
                  fontSize: '12px', 
                  color: '#6c757d',
                  fontStyle: 'italic'
                }}>
                  {language === 'en' 
                    ? 'Ready to create your diary entry based on our conversation'
                    : '准备根据我们的对话创建你的日记条目'
                  }
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Historical Diary Modal */}
      {showHistoricalDiary && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '10px',
            maxWidth: '80%',
            maxHeight: '80%',
            overflow: 'auto',
            boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0 }}>
                {language === 'en' ? `Diary for ${selectedDate}` : `${selectedDate} 的日记`}
              </h3>
              <button
                onClick={() => setShowHistoricalDiary(false)}
                style={{
                  padding: '5px 10px',
                  border: 'none',
                  borderRadius: '5px',
                  backgroundColor: '#dc3545',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                ✕
              </button>
            </div>
            
            {selectedDateSessions.map((entry, index) => (
              <div key={index} style={{
                backgroundColor: '#f9f9f9', 
                padding: '20px', 
                borderRadius: '10px',
                marginBottom: '15px',
                lineHeight: '1.6',
                border: '1px solid #e0e0e0',
              }}>
                {/* Mode indicator and action buttons header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  {entry.mode && (
                    <div style={{
                      fontSize: '11px',
                      color: '#666',
                      backgroundColor: entry.mode === 'guided' ? '#e3f2fd' : '#f3e5f5',
                      padding: '3px 8px',
                      borderRadius: '12px',
                      fontWeight: '500'
                    }}>
                      {entry.mode === 'guided' 
                        ? (language === 'en' ? '📝 Guided Mode' : '📝 引导模式')
                        : (language === 'en' ? '💬 Casual Mode' : '💬 休闲模式')
                      }
                    </div>
                  )}
                  
                  {/* Edit and Delete buttons */}
                  <div style={{ display: 'flex', gap: '5px' }}>
                    {editingEntryId === entry.id ? (
                      <>
                        <button
                          onClick={() => saveEntryEdit(entry.id, entry.mode)}
                          disabled={loading}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                          }}
                        >
                          ✓ {language === 'en' ? 'Save' : '保存'}
                        </button>
                        <button
                          onClick={cancelEditingEntry}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#6c757d',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                          }}
                        >
                          ✕ {language === 'en' ? 'Cancel' : '取消'}
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => startEditingEntry(entry.id, entry.content || entry.final_diary || entry.composed_diary)}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                          }}
                        >
                          ✏️ {language === 'en' ? 'Edit' : '编辑'}
                        </button>
                        <button
                          onClick={() => deleteEntry(entry.id, entry.mode)}
                          disabled={loading}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#dc3545',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                          }}
                        >
                          🗑️ {language === 'en' ? 'Delete' : '删除'}
                        </button>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Content area */}
                {editingEntryId === entry.id ? (
                  <textarea
                    value={editingContent}
                    onChange={(e) => setEditingContent(e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: '120px',
                      padding: '12px',
                      border: '2px solid #007bff',
                      borderRadius: '6px',
                      fontSize: '14px',
                      lineHeight: '1.6',
                      resize: 'vertical',
                      fontFamily: 'inherit',
                      outline: 'none',
                    }}
                    placeholder={language === 'en' ? 'Edit your diary entry...' : '编辑你的日记条目...'}
                  />
                ) : (
                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {entry.content || entry.final_diary || entry.composed_diary}
                  </div>
                )}
                
                <div style={{ 
                  marginTop: '10px', 
                  fontSize: '12px', 
                  color: '#888',
                  borderTop: '1px solid #e0e0e0',
                  paddingTop: '10px'
                }}>
                  {language === 'en' ? 'Created:' : '创建时间:'} {new Date(entry.created_at || entry.completed_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GuidedChat;