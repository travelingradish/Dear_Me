import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';
import { llmAPI, diaryAPI, guidedDiaryAPI } from '../utils/api.ts';
import { Message } from '../types/index.ts';
import SimpleCalendar from './SimpleCalendar.tsx';
import DiaryModal from './DiaryModal.tsx';
import Sidebar from './Sidebar.tsx';

interface SimpleChatProps {
  onSwitchToGuided?: () => void;
  onSwitchToFreeEntry?: () => void;
}

const SimpleChat: React.FC<SimpleChatProps> = ({ onSwitchToGuided, onSwitchToFreeEntry }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const { language } = useAuth();
  const [showDiary, setShowDiary] = useState(false);
  const [diary, setDiary] = useState('');
  const [editedDiary, setEditedDiary] = useState('');
  const [isEditingDiary, setIsEditingDiary] = useState(false);
  const [selectedDateDiaries, setSelectedDateDiaries] = useState<any[]>([]);
  const [showHistoricalDiary, setShowHistoricalDiary] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  
  // Conversation modal state
  const [showConversationModal, setShowConversationModal] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  const [conversationLoading, setConversationLoading] = useState(false);

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
  
  const { user, logout } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const characterName = user?.ai_character_name || "AI Assistant";
    const welcomeMessage: Message = {
      id: '1',
      content: language === 'en' 
        ? `Hi, ${characterName} here. How are you feeling today? 😊`
        : `你好！😊 我是${characterName}。我在这里帮你回顾今天。你现在想聊什么？`,
      sender: 'assistant',
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, [language, user?.ai_character_name]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const conversationHistory = messages.map(msg => ({
        type: msg.sender === 'user' ? 'user' : 'assistant',
        message: msg.content,
        timestamp: msg.timestamp.toISOString(),
      }));

      const response = await llmAPI.sendMessage(inputMessage, conversationHistory, language);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: language === 'en'
          ? "Sorry, I'm having trouble connecting right now. Please try again."
          : "抱歉，我现在连接有问题。请重试。",
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const generateDiary = async () => {
    setLoading(true);
    try {
      const answers = messages
        .filter(msg => msg.sender === 'user')
        .reduce((acc, msg, index) => {
          acc[`response_${index}`] = msg.content;
          return acc;
        }, {} as Record<string, string>);

      const conversationHistory = messages.map(msg => ({
        type: msg.sender === 'user' ? 'user' : 'assistant',
        message: msg.content,
        timestamp: msg.timestamp.toISOString(),
      }));

      const response = await diaryAPI.generate(answers, conversationHistory, language);
      setDiary(response.diary);
      setEditedDiary(response.diary);
      setIsEditingDiary(false);
      setShowDiary(true);
    } catch (error) {
      console.error('Error generating diary:', error);
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

  const startEditing = () => {
    setIsEditingDiary(true);
  };

  const cancelEditing = () => {
    setEditedDiary(diary); // Reset to original
    setIsEditingDiary(false);
  };

  const saveDiaryEdit = () => {
    setDiary(editedDiary); // Save the edited version
    setIsEditingDiary(false);
  };

  const handleDateSelect = (date: string, entries: any[]) => {
    setSelectedDate(date);
    setSelectedDateDiaries(entries);
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
      
      if (mode === 'casual' || mode === 'free_entry') {
        const numericId = parseInt(entryId.replace(`${mode}_`, ''));
        await diaryAPI.editEntry(numericId, editingContent);
      } else if (mode === 'guided') {
        const numericId = parseInt(entryId.replace('guided_', ''));
        await guidedDiaryAPI.editSessionDiary(numericId, editingContent);
      }
      
      // Update local state
      setSelectedDateDiaries(prev => 
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
      setSelectedDateDiaries(prev => 
        prev.filter(entry => entry.id !== entryId)
      );
      
      // If no entries left, close modal
      if (selectedDateDiaries.length <= 1) {
        setShowHistoricalDiary(false);
      }
    } catch (error) {
      console.error('Error deleting entry:', error);
      alert(language === 'en' ? 'Failed to delete entry' : '删除失败');
    } finally {
      setLoading(false);
    }
  };

  const viewConversation = async (entryId: string, mode: 'guided' | 'casual') => {
    setConversationLoading(true);
    setShowConversationModal(true);
    
    try {
      let response;
      if (mode === 'guided') {
        // For guided mode, get the session details
        response = await guidedDiaryAPI.getSession(parseInt(entryId));
        setConversationHistory(response.conversation_history || []);
      } else {
        // For casual mode, use the existing API endpoint to get conversation history
        try {
          response = await diaryAPI.getConversation(parseInt(entryId));
          console.log('Casual conversation response:', response);
          
          if (response.success && response.conversation_history) {
            if (Array.isArray(response.conversation_history) && response.conversation_history.length > 0) {
              // Convert the conversation history format to match the expected format
              const formattedHistory = response.conversation_history.map((msg: any) => ({
                role: msg.type === 'user' ? 'user' : 'assistant',
                content: msg.message || msg.content || msg.text || 'Empty message',
                created_at: msg.timestamp || msg.created_at || new Date().toISOString()
              }));
              console.log('Formatted history:', formattedHistory);
              setConversationHistory(formattedHistory);
            } else {
              // Empty conversation history
              setConversationHistory([{
                role: 'system',
                content: language === 'en' 
                  ? 'This diary entry has no conversation history.'
                  : '此日记条目没有对话历史。',
                created_at: new Date().toISOString()
              }]);
            }
          } else {
            // API returned success=false or no conversation_history field
            setConversationHistory([{
              role: 'system',
              content: language === 'en' 
                ? 'No conversation history found for this diary entry.'
                : '此日记条目没有找到对话历史。',
              created_at: new Date().toISOString()
            }]);
          }
        } catch (error) {
          console.error('Error loading casual conversation:', error);
          // Fallback for when API doesn't exist or fails
          setConversationHistory([{
            role: 'system',
            content: language === 'en' 
              ? 'Unable to load conversation history for this entry. Error: ' + (error as Error).message
              : '无法加载此条目的对话历史。错误：' + (error as Error).message,
            created_at: new Date().toISOString()
          }]);
        }
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
      setConversationHistory([]);
    } finally {
      setConversationLoading(false);
    }
  };

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    height: '100vh',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  };

  const mainStyle: React.CSSProperties = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f9f9f9',
  };

  const headerStyle: React.CSSProperties = {
    backgroundColor: 'white',
    padding: '20px',
    borderBottom: '1px solid #e0e0e0',
  };

  const messagesStyle: React.CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
  };

  const messageStyle = (sender: string): React.CSSProperties => ({
    marginBottom: '15px',
    display: 'flex',
    justifyContent: sender === 'user' ? 'flex-end' : 'flex-start',
  });

  const bubbleStyle = (sender: string): React.CSSProperties => ({
    maxWidth: '70%',
    padding: '12px 16px',
    borderRadius: '18px',
    backgroundColor: sender === 'user' ? '#667eea' : 'white',
    color: sender === 'user' ? 'white' : '#333',
    border: sender === 'assistant' ? '1px solid #e0e0e0' : 'none',
  });

  const inputAreaStyle: React.CSSProperties = {
    backgroundColor: 'white',
    padding: '20px',
    borderTop: '1px solid #e0e0e0',
    display: 'flex',
    gap: '10px',
  };

  const inputStyle: React.CSSProperties = {
    flex: 1,
    padding: '12px 16px',
    border: '2px solid #e0e0e0',
    borderRadius: '25px',
    fontSize: '16px',
    outline: 'none',
  };

  const buttonStyle: React.CSSProperties = {
    backgroundColor: '#667eea',
    color: 'white',
    border: 'none',
    borderRadius: '50%',
    width: '45px',
    height: '45px',
    cursor: 'pointer',
    fontSize: '18px',
  };

  const modalStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  };

  const modalContentStyle: React.CSSProperties = {
    backgroundColor: 'white',
    borderRadius: '15px',
    padding: '30px',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '80vh',
    overflowY: 'auto',
  };

  return (
    <div style={containerStyle}>
      {/* Shared Sidebar */}
      <Sidebar
        currentMode="casual"
        onSwitchToGuided={onSwitchToGuided}
        onSwitchToFreeEntry={onSwitchToFreeEntry}
      >
        {/* Calendar */}
        <SimpleCalendar 
          language={language}
          onDateSelect={handleDateSelect}
        />

        <button
          onClick={generateDiary}
          disabled={loading || messages.filter(m => m.sender === 'user').length < 2}
          style={{
            width: '100%',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            padding: '12px',
            borderRadius: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading || messages.filter(m => m.sender === 'user').length < 2 ? 0.5 : 1,
          }}
        >
          📖 {language === 'en' ? 'Generate Diary' : '生成日记'}
        </button>
      </Sidebar>

      {/* Main Chat */}
      <div style={mainStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <h1 style={{ margin: 0, color: '#667eea', fontWeight: '300' }}>Dear Me</h1>
          <p style={{ margin: '2px 0 0 0', color: '#999', fontSize: '0.8rem', fontStyle: 'italic' }}>
            Be Here, Be Now, Be You -- in a space you call your own
          </p>
        </div>

        {/* Messages */}
        <div style={messagesStyle}>
          {messages.map((message) => (
            <div key={message.id} style={messageStyle(message.sender)}>
              <div style={bubbleStyle(message.sender)}>
                <p style={{ margin: 0, fontSize: '14px', textAlign: 'left' }}>{message.content}</p>
                <p style={{ 
                  margin: '5px 0 0 0', 
                  fontSize: '12px', 
                  opacity: 0.7,
                  textAlign: 'left'
                }}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}
          
          {loading && (
            <div style={messageStyle('assistant')}>
              <div style={bubbleStyle('assistant')}>
                <p style={{ margin: 0, fontSize: '14px', textAlign: 'left' }}>
                  {language === 'en' ? 'Thinking...' : '思考中...'}
                </p>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={inputAreaStyle}>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={language === 'en' ? 'Type your message...' : '输入你的消息...'}
            style={inputStyle}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !inputMessage.trim()}
            style={{
              ...buttonStyle,
              opacity: loading || !inputMessage.trim() ? 0.5 : 1,
              cursor: loading || !inputMessage.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            ➤
          </button>
        </div>
      </div>

      {/* Diary Modal */}
      {showDiary && (
        <div style={modalStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ marginBottom: '20px', color: '#333' }}>
              📖 {language === 'en' ? 'Your Personal Diary' : '你的个人日记'}
              {!isEditingDiary && (
                <button
                  onClick={startEditing}
                  style={{
                    marginLeft: '15px',
                    padding: '5px 10px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  ✏️ {language === 'en' ? 'Edit' : '编辑'}
                </button>
              )}
            </h2>
            
            {isEditingDiary ? (
              <div style={{ marginBottom: '20px' }}>
                <textarea
                  value={editedDiary}
                  onChange={(e) => setEditedDiary(e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: '300px',
                    padding: '20px',
                    border: '2px solid #007bff',
                    borderRadius: '10px',
                    fontSize: '16px',
                    lineHeight: '1.6',
                    resize: 'vertical',
                    fontFamily: 'inherit',
                    outline: 'none',
                  }}
                  placeholder={language === 'en' ? 'Edit your diary...' : '编辑你的日记...'}
                />
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                  <button
                    onClick={saveDiaryEdit}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '14px',
                    }}
                  >
                    ✅ {language === 'en' ? 'Save Changes' : '保存更改'}
                  </button>
                  <button
                    onClick={cancelEditing}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '14px',
                    }}
                  >
                    ❌ {language === 'en' ? 'Cancel' : '取消'}
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ 
                backgroundColor: '#f9f9f9', 
                padding: '20px', 
                borderRadius: '10px',
                marginBottom: '20px',
                lineHeight: '1.4',
                whiteSpace: 'pre-wrap',
                border: '1px solid #e0e0e0',
                textAlign: 'left'
              }}>
                {formatTextWithParagraphSpacing(diary)}
              </div>
            )}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowDiary(false)}
                style={{
                  padding: '10px 20px',
                  border: '1px solid #ccc',
                  backgroundColor: 'white',
                  borderRadius: '5px',
                  cursor: 'pointer',
                }}
              >
                {language === 'en' ? 'Close' : '关闭'}
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(diary);
                  alert(language === 'en' ? 'Diary copied to clipboard!' : '日记已复制到剪贴板！');
                }}
                disabled={isEditingDiary}
                style={{
                  padding: '10px 20px',
                  backgroundColor: isEditingDiary ? '#6c757d' : '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: isEditingDiary ? 'not-allowed' : 'pointer',
                  opacity: isEditingDiary ? 0.6 : 1,
                }}
              >
                📋 {language === 'en' ? 'Copy' : '复制'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Historical Diary Modal */}
      <DiaryModal
        isOpen={showHistoricalDiary}
        onClose={() => setShowHistoricalDiary(false)}
        selectedDate={selectedDate}
        entries={selectedDateDiaries.map(entry => ({
          id: entry.id,
          content: entry.content,
          mode: entry.mode as 'guided' | 'casual' | 'free_entry',
          created_at: entry.created_at
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
                💬 {language === 'en' ? 'Conversation History' : '对话历史'}
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
            
            {/* Conversation Content */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '20px'
            }}>
              {conversationLoading ? (
                <div style={{ textAlign: 'center', color: '#666' }}>
                  {language === 'en' ? 'Loading conversation...' : '加载对话中...'}
                </div>
              ) : conversationHistory.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#666' }}>
                  {language === 'en' ? 'No conversation history found.' : '未找到对话历史。'}
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  {conversationHistory.map((message: any, index: number) => (
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
                        backgroundColor: message.role === 'user' ? '#667eea' : message.role === 'system' ? '#fff3cd' : '#f8f9fa',
                        color: message.role === 'user' ? 'white' : '#333',
                        border: message.role !== 'user' ? '1px solid #e0e0e0' : 'none'
                      }}>
                        <div style={{ fontSize: '14px', lineHeight: '1.5', textAlign: 'left' }}>
                          {message.content}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default SimpleChat;