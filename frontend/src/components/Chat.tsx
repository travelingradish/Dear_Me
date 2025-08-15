import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { llmAPI, diaryAPI } from '../utils/api';
import { Message } from '../types';
import { Send, MessageCircle, BookOpen, LogOut, User, Loader } from 'lucide-react';

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [showDiary, setShowDiary] = useState(false);
  const [diary, setDiary] = useState('');
  const [conversationCount, setConversationCount] = useState(0);
  
  const { user, logout } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add welcome message
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
      // Build conversation history for API (all previous messages)
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
      setConversationCount(prev => prev + 1);

      // Show diary option after several exchanges
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
      // Extract answers from conversation
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

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <User className="text-white" size={20} />
              </div>
              <div className="ml-3">
                <h3 className="font-semibold text-gray-800">{user?.username}</h3>
                <p className="text-sm text-gray-600">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="en">English</option>
              <option value="zh">中文</option>
            </select>
          </div>

          <button
            onClick={generateDiary}
            disabled={loading || messages.filter(m => m.sender === 'user').length < 2}
            className="w-full bg-gradient-to-r from-green-500 to-blue-600 text-white py-3 rounded-lg font-medium hover:from-green-600 hover:to-blue-700 focus:ring-4 focus:ring-green-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <BookOpen className="mr-2" size={20} />
            {language === 'en' ? 'Generate Diary' : '生成日记'}
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-6">
          <div className="flex items-center">
            <MessageCircle className="text-blue-500 mr-3" size={24} />
            <h1 className="text-2xl font-light text-blue-500">
              Dear Me
            </h1>
          </div>
          <p className="text-gray-600 mt-1">
            {language === 'en' 
              ? 'Tell me about your day and let me help you reflect'
              : '告诉我你的一天，让我帮你反思'
            }
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p className={`text-xs mt-1 ${
                  message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 text-gray-800 px-4 py-2 rounded-2xl flex items-center">
                <Loader className="animate-spin mr-2" size={16} />
                <span className="text-sm">
                  {language === 'en' ? 'Thinking...' : '思考中...'}
                </span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-6">
          <div className="flex space-x-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={language === 'en' ? 'Type your message...' : '输入你的消息...'}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !inputMessage.trim()}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-600 hover:to-purple-700 focus:ring-4 focus:ring-blue-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Diary Modal */}
      {showDiary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                <BookOpen className="mr-3" size={24} />
                {language === 'en' ? 'Your Personal Diary' : '你的个人日记'}
              </h2>
            </div>
            <div className="p-6">
              <div className="prose max-w-none">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{diary}</p>
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowDiary(false)}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {language === 'en' ? 'Close' : '关闭'}
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(diary);
                  alert(language === 'en' ? 'Diary copied to clipboard!' : '日记已复制到剪贴板！');
                }}
                className="px-6 py-2 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-lg hover:from-green-600 hover:to-blue-700 transition-all"
              >
                {language === 'en' ? 'Copy' : '复制'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;