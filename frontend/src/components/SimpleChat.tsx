import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';
import { llmAPI, diaryAPI, guidedDiaryAPI, unifiedDiaryAPI } from '../utils/api.ts';
import { Message } from '../types/index.ts';
import SimpleCalendar from './SimpleCalendar.tsx';

interface SimpleChatProps {
  onSwitchToGuided?: () => void;
}

const SimpleChat: React.FC<SimpleChatProps> = ({ onSwitchToGuided }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [showDiary, setShowDiary] = useState(false);
  const [diary, setDiary] = useState('');
  const [editedDiary, setEditedDiary] = useState('');
  const [isEditingDiary, setIsEditingDiary] = useState(false);
  const [conversationCount, setConversationCount] = useState(0);
  const [selectedDateDiaries, setSelectedDateDiaries] = useState<any[]>([]);
  const [showHistoricalDiary, setShowHistoricalDiary] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedModel, setSelectedModel] = useState('llama3.1:8b');
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  
  const { user, logout } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const welcomeMessage: Message = {
      id: '1',
      content: language === 'en' 
        ? "Hi there! 😊 I'm here to help you reflect on your day. What's on your mind today?"
        : "你好！😊 我在这里帮你回顾今天。你现在想聊什么？",
      sender: 'assistant',
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, [language]);

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

      const response = await llmAPI.sendMessage(inputMessage, conversationHistory, language, selectedModel);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationCount(prev => prev + 1);

      if (conversationCount >= 4) {
        setTimeout(() => {
          const diaryPrompt: Message = {
            id: (Date.now() + 2).toString(),
            content: language === 'en'
              ? "Would you like me to create a personal diary entry from our conversation? 📖"
              : "你想让我从我们的对话中创建一个个人日记吗？📖",
            sender: 'assistant',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, diaryPrompt]);
        }, 2000);
      }
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
      
      if (mode === 'casual') {
        const numericId = parseInt(entryId.replace('casual_', ''));
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
      
      if (mode === 'casual') {
        const numericId = parseInt(entryId.replace('casual_', ''));
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

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    height: '100vh',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  };

  const sidebarStyle: React.CSSProperties = {
    width: '300px',
    backgroundColor: 'white',
    borderRight: '1px solid #e0e0e0',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
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
      {/* Sidebar */}
      <div style={sidebarStyle}>
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
          {onSwitchToGuided && (
            <button
              onClick={onSwitchToGuided}
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
              {language === 'en' ? 'Try Guided Mode' : '尝试引导模式'}
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
      </div>

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
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                border: '1px solid #e0e0e0',
              }}>
                {diary}
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
      {showHistoricalDiary && (
        <div style={modalStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ marginBottom: '20px', color: '#333' }}>
              📅 {language === 'en' ? `Diary for ${selectedDate}` : `${selectedDate} 的日记`}
            </h2>
            
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {selectedDateDiaries.map((entry, index) => (
                <div key={entry.id || index} style={{ 
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
                            onClick={() => startEditingEntry(entry.id, entry.content)}
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
                      {entry.content}
                    </div>
                  )}
                  
                  <div style={{ 
                    marginTop: '10px', 
                    fontSize: '12px', 
                    color: '#888',
                    borderTop: '1px solid #e0e0e0',
                    paddingTop: '10px'
                  }}>
                    {language === 'en' ? 'Created:' : '创建时间:'} {new Date(entry.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button
                onClick={() => setShowHistoricalDiary(false)}
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
              {selectedDateDiaries.length > 0 && (
                <button
                  onClick={() => {
                    const allDiaries = selectedDateDiaries.map(entry => entry.content).join('\n\n---\n\n');
                    navigator.clipboard.writeText(allDiaries);
                    alert(language === 'en' ? 'Diaries copied to clipboard!' : '日记已复制到剪贴板！');
                  }}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                  }}
                >
                  📋 {language === 'en' ? 'Copy All' : '复制全部'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleChat;