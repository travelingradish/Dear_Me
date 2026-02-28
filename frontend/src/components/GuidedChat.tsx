import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import { guidedDiaryAPI, diaryAPI, unifiedDiaryAPI } from '../utils/api.ts';
import { GuidedDiarySession, ConversationMessage, GuidedDiaryResponse } from '../types/index.ts';
import SimpleCalendar from './SimpleCalendar.tsx';
import DiaryModal from './DiaryModal.tsx';
import Sidebar from './Sidebar.tsx';
import '../styles/responsive.css';

interface GuidedChatProps {
  onSwitchToLegacy: () => void;
  onSwitchToFreeEntry?: () => void;
}

const GuidedChat: React.FC<GuidedChatProps> = ({ onSwitchToLegacy, onSwitchToFreeEntry }) => {
  const [session, setSession] = useState<GuidedDiarySession | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const { language } = useAuth();
  const [isEditingDiary, setIsEditingDiary] = useState(false);
  const [editedDiary, setEditedDiary] = useState('');
  const [selectedDateSessions, setSelectedDateSessions] = useState<any[]>([]);
  const [showHistoricalDiary, setShowHistoricalDiary] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [showConversationModal, setShowConversationModal] = useState(false);
  const [conversationForModal, setConversationForModal] = useState<ConversationMessage[]>([]);

  // Helper function to format text with conservative paragraph spacing
  const formatTextWithParagraphSpacing = (text: string) => {
    if (!text) return text;
    
    // Only create paragraph breaks at major transitions, not every sentence
    // Look for existing paragraph breaks first
    if (text.includes('\n\n')) {
      return text; // Text already has proper paragraph formatting
    }
    
    // Very conservative paragraph detection - only break at major topic shifts
    let formattedText = text
      // Break before clear temporal transitions (new time periods)
      .replace(/ (After wrapping up|Later that day|In the evening|During the morning|Throughout the day)/g, '\n\n$1')
      // Break before reflection statements
      .replace(/ (As I reflect|Looking back|What struck me)/g, '\n\n$1');
    
    return formattedText;
  };
  const { user, logout, updateCharacterName } = useAuth();
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

  useEffect(() => {
    // Restart session when language changes (if there's an active session)
    if (session && !session.is_complete) {
      console.log('Language changed to:', language, 'restarting session...');
      startNewSession();
    }
  }, [language]);

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
      
      // Debug: Log the language being sent
      console.log('Starting new session with language:', language);
      
      const response = await guidedDiaryAPI.startSession(language);
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
      
      // Log detailed error information
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
      }
      
      // If it's a fetch error, log response details
      if (error && typeof error === 'object' && 'response' in error) {
        console.error('Response status:', (error as any).response?.status);
        console.error('Response data:', (error as any).response?.data);
      }
      
      // Show user-friendly error message
      alert(`Failed to start guided session. Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
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
    const currentInput = inputMessage;
    setInputMessage('');
    setLoading(true);

    // Check if user is explicitly requesting diary generation
    const diaryGenerationKeywords = language === 'en' 
      ? ['generate diary', 'create diary', 'write diary', 'make diary', 'diary now', 'generate my diary', 'create my diary', 'generate a diary', 'create a diary', 'diary for me', 'make a diary']
      : ['生成日记', '创建日记', '写日记', '做日记', '现在日记', '生成我的日记', '创建我的日记', '生成一个日记', '创建一个日记', '为我生成日记'];
    
    const requestingDiary = diaryGenerationKeywords.some(keyword => 
      currentInput.toLowerCase().includes(keyword.toLowerCase())
    );

    if (requestingDiary && session.current_intent !== 'COMPOSE' && !session.is_complete) {
      // User wants to generate diary early, trigger diary generation
      try {
        const response = await guidedDiaryAPI.sendMessage(
          session.id,
          "I'm ready to generate my diary now.", // Trigger message
          language
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

          if (response.is_complete && response.final_diary) {
            setEditedDiary(response.final_diary);
          }
        }
        setLoading(false);
        return;
      } catch (error) {
        console.error('Error generating diary:', error);
        // Fall through to normal message handling
      }
    }

    try {
      const response: GuidedDiaryResponse = await guidedDiaryAPI.sendMessage(
        session.id,
        inputMessage,
        language
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

  const viewConversation = async (sessionId: string, mode: 'guided' | 'casual' = 'guided') => {
    try {
      setLoading(true);
      let response;
      
      if (mode === 'guided') {
        response = await guidedDiaryAPI.getSession(sessionId);
      } else {
        response = await diaryAPI.getConversation(parseInt(sessionId));
      }
      
      if (response.success) {
        // Convert casual mode conversation history to the same format as guided mode
        let conversationHistory = response.conversation_history || [];
        
        if (mode === 'casual' && conversationHistory.length > 0) {
          // Casual mode conversation history format might be different, so normalize it
          conversationHistory = conversationHistory.map((msg: any) => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.message || msg.content,
            created_at: msg.timestamp || new Date().toISOString()
          }));
        }
        
        setConversationForModal(conversationHistory);
        setShowConversationModal(true);
      }
    } catch (error) {
      console.error('Error fetching conversation:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveEntryEdit = async (entryId: string, mode: string) => {
    try {
      setLoading(true);
      
      if (mode === 'casual' || mode === 'free_entry') {
        const numericId = parseInt(entryId.replace(`${mode}_`, ''));
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
      
      if (mode === 'casual' || mode === 'free_entry') {
        const numericId = parseInt(entryId.replace(`${mode}_`, ''));
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
    <div className="app-layout">
      {/* Shared Sidebar */}
      <Sidebar
        currentMode="guided"
        onSwitchToSimple={onSwitchToLegacy}
        onSwitchToFreeEntry={onSwitchToFreeEntry}
      >
        <SimpleCalendar 
          language={language}
          onDateSelect={handleDateSelect}
        />

        <button
          onClick={session && !session.is_complete ? async () => {
            // Generate diary if there's an active session
            if (!session) return;
            
            try {
              setLoading(true);
              const response = await guidedDiaryAPI.sendMessage(
                session.id,
                "I'm ready to generate my diary now.", // Trigger message
                language
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

                if (response.is_complete && response.final_diary) {
                  setEditedDiary(response.final_diary);
                }
              }
            } catch (error) {
              console.error('Error generating diary:', error);
            } finally {
              setLoading(false);
            }
          } : startNewSession}
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
          {session && !session.is_complete 
            ? (loading ? '...' : (language === 'en' ? '📝 Generate My Diary' : '📝 生成我的日记'))
            : ('✨ ' + (language === 'en' ? 'Start Fresh Session' : '开始新对话'))
          }
        </button>
      </Sidebar>

      {/* Main Chat Area */}
      <div className="main-content">
        {/* Header */}
        <div className="main-header">
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
                  <div
                    className="message-bubble"
                    style={{
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
                  <div
                    className="message-bubble"
                    style={{
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
                        lineHeight: '1.4',
                        textAlign: 'left'
                      }}>
                        {formatTextWithParagraphSpacing(session.final_diary)}
                      </div>
                      <button
                        onClick={startEditing}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#007bff',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          marginRight: '10px'
                        }}
                      >
                        {language === 'en' ? 'Edit' : '编辑'}
                      </button>
                      <button
                        onClick={() => viewConversation(session.id.toString(), 'guided')}
                        disabled={loading}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#17a2b8',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer'
                        }}
                      >
                        💬 {language === 'en' ? 'View Conversation' : '查看对话'}
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
                        language
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
      <DiaryModal
        isOpen={showHistoricalDiary}
        onClose={() => setShowHistoricalDiary(false)}
        selectedDate={selectedDate}
        entries={selectedDateSessions.map(entry => ({
          id: entry.id,
          content: entry.content || entry.final_diary || entry.composed_diary,
          mode: entry.mode as 'guided' | 'casual' | 'free_entry',
          created_at: entry.created_at || entry.completed_at,
          final_diary: entry.final_diary
        }))}
        language={language}
        editingEntryId={editingEntryId}
        editingContent={editingContent}
        loading={loading}
        onStartEditing={startEditingEntry}
        onCancelEditing={cancelEditingEntry}
        onSaveEdit={saveEntryEdit}
        onDeleteEntry={deleteEntry}
        onViewConversation={(sessionId, mode) => {
          if (mode === 'guided') {
            viewConversation(sessionId.replace('guided_', ''), 'guided');
          } else {
            // For casual and free_entry modes, use casual API
            const numericId = sessionId.replace(/^(casual|free_entry)_/, '');
            viewConversation(numericId, 'casual');
          }
        }}
        setEditingContent={setEditingContent}
      />

      {/* Conversation Modal */}
      {showConversationModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            width: '90%',
            maxWidth: '800px',
            maxHeight: '80%',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '20px',
              borderBottom: '1px solid #e0e0e0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h3 style={{ margin: 0, color: '#333' }}>
                💬 {language === 'en' ? 'Original Conversation' : '原始对话'}
              </h3>
              <button
                onClick={() => setShowConversationModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666',
                  padding: '0',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ×
              </button>
            </div>

            {/* Modal Content */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '20px'
            }}>
              {conversationForModal.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#666' }}>
                  {language === 'en' ? 'No conversation history found.' : '未找到对话历史。'}
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  {conversationForModal.map((message, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
                      }}
                    >
                      <div style={{
                        maxWidth: '70%',
                        padding: '12px 16px',
                        borderRadius: '18px',
                        backgroundColor: message.role === 'user' ? '#667eea' : '#f8f9fa',
                        color: message.role === 'user' ? 'white' : '#333',
                        border: message.role === 'assistant' ? '1px solid #e0e0e0' : 'none'
                      }}>
                        <div style={{ fontSize: '14px', lineHeight: '1.5', textAlign: 'left' }}>
                          {message.content}
                        </div>
                        <div style={{
                          fontSize: '12px',
                          opacity: 0.7,
                          marginTop: '5px'
                        }}>
                          {new Date(message.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '20px',
              borderTop: '1px solid #e0e0e0',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '10px'
            }}>
              <button
                onClick={() => setShowConversationModal(false)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                {language === 'en' ? 'Close' : '关闭'}
              </button>
              <button
                onClick={() => {
                  const conversationText = conversationForModal
                    .map(msg => `${msg.role === 'user' ? 'You' : 'Assistant'}: ${msg.content}`)
                    .join('\n\n');
                  navigator.clipboard.writeText(conversationText);
                  alert(language === 'en' ? 'Conversation copied to clipboard!' : '对话已复制到剪贴板！');
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#17a2b8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                📋 {language === 'en' ? 'Copy Conversation' : '复制对话'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default GuidedChat;