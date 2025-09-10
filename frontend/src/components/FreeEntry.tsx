import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';
import { freeEntryAPI, unifiedDiaryAPI, guidedDiaryAPI, diaryAPI } from '../utils/api.ts';
import SimpleCalendar from './SimpleCalendar.tsx';
import DiaryModal from './DiaryModal.tsx';
import Sidebar from './Sidebar.tsx';

interface FreeEntryProps {
  onSwitchToGuided?: () => void;
  onSwitchToSimple?: () => void;
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

export default function FreeEntry({ onSwitchToGuided, onSwitchToSimple }: FreeEntryProps) {
  const { user, language } = useAuth();
  const [originalText, setOriginalText] = useState('');
  const [currentText, setCurrentText] = useState('');
  const [trueOriginalText, setTrueOriginalText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showImproveOptions, setShowImproveOptions] = useState(false);
  const [savedEntryId, setSavedEntryId] = useState<number | null>(null);
  const [showComparison, setShowComparison] = useState(false);
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

  const placeholders = {
    en: "Write freely about your day, thoughts, feelings, or anything on your mind...\n\nThis is your space to express yourself without any constraints. When you're done, I can help you polish your writing if you'd like.",
    zh: "自由地写下你今天的经历、想法、感受或任何心事...\n\n这是你自由表达的空间，没有任何限制。写完后，如果需要的话，我可以帮你润色文字。"
  };

  const texts = {
    en: {
      title: "Free Entry Mode",
      subtitle: "自由书写",
      wordCount: "words",
      charCount: "characters",
      correctGrammar: "Fix Grammar",
      improveGeneral: "Improve Writing",
      improveClarity: "Improve Clarity", 
      improveFlow: "Improve Flow",
      improveVocabulary: "Enhance Vocabulary",
      save: "Save Entry",
      showOptions: "Advanced Options",
      hideOptions: "Hide Advanced Options",
      working: "Working...",
      saved: "Entry Saved!",
      showComparison: "Show Original vs Current",
      hideComparison: "Hide Comparison",
      originalVersion: "Original Version",
      currentVersion: "Current Version",
      noChanges: "No changes were made to your text.",
      reset: "Reset to Original",
      switchToGuided: "Switch to Guided Mode",
      switchToSimple: "Switch to Simple Chat"
    },
    zh: {
      title: "自由书写模式",
      subtitle: "Free Entry",
      wordCount: "字",
      charCount: "字符",
      correctGrammar: "语法纠错",
      improveGeneral: "提升写作",
      improveClarity: "提升清晰度",
      improveFlow: "改善流畅性",
      improveVocabulary: "增强词汇",
      save: "保存日记",
      showOptions: "高级选项",
      hideOptions: "隐藏高级选项",
      working: "处理中...",
      saved: "日记已保存！",
      showComparison: "显示原文对比",
      hideComparison: "隐藏对比",
      originalVersion: "原始版本",
      currentVersion: "当前版本",
      noChanges: "文本没有任何修改。",
      reset: "恢复原文",
      switchToGuided: "切换到引导模式",
      switchToSimple: "切换到简单对话"
    }
  };

  const t = texts[language as keyof typeof texts];

  const getWordCount = (text: string) => {
    if (language === 'zh') {
      // For Chinese, count characters (excluding spaces and punctuation)
      return text.replace(/[\s\p{P}]/gu, '').length;
    } else {
      // For English, count words
      return text.trim().split(/\s+/).filter(word => word.length > 0).length;
    }
  };

  const handleCorrectGrammar = async () => {
    if (!currentText.trim()) return;
    
    // Capture the ORIGINAL text BEFORE making any API calls or state changes
    const originalTextBeforeCorrection = currentText;
    console.log('Capturing ORIGINAL text before correction:', originalTextBeforeCorrection);
    
    // If this is the first correction, save the true original
    if (!trueOriginalText) {
      setTrueOriginalText(originalTextBeforeCorrection);
      console.log('Saving TRUE original text:', originalTextBeforeCorrection);
    }
    
    setIsLoading(true);
    try {
      const response = await freeEntryAPI.correctGrammar(currentText, language);
      
      if (response.success) {
        if (response.corrected_text === currentText) {
          alert(t.noChanges);
        } else {
          // Set the original text to what user actually typed (for immediate comparison)
          setOriginalText(originalTextBeforeCorrection);
          // Set the current text to the corrected version
          setCurrentText(response.corrected_text);
          // Show comparison after both state updates
          setTimeout(() => setShowComparison(true), 200);
        }
      }
    } catch (error) {
      console.error('Grammar correction error:', error);
      alert('Failed to correct grammar. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImproveWriting = async (improvementType: string) => {
    if (!currentText.trim()) return;
    
    // Capture the ORIGINAL text BEFORE making any API calls or state changes
    const originalTextBeforeImprovement = currentText;
    console.log('Capturing ORIGINAL text before improvement:', originalTextBeforeImprovement);
    
    // If this is the first improvement, save the true original
    if (!trueOriginalText) {
      setTrueOriginalText(originalTextBeforeImprovement);
      console.log('Saving TRUE original text:', originalTextBeforeImprovement);
    }
    
    setIsLoading(true);
    try {
      const response = await freeEntryAPI.improveWriting(currentText, language, improvementType);
      
      if (response.success) {
        if (response.improved_text === currentText) {
          alert(t.noChanges);
        } else {
          // Set the original text to what user actually typed (for immediate comparison)
          setOriginalText(originalTextBeforeImprovement);
          // Set the current text to the improved version
          setCurrentText(response.improved_text);
          // Show comparison after both state updates
          setTimeout(() => setShowComparison(true), 200);
        }
      }
    } catch (error) {
      console.error('Writing improvement error:', error);
      alert('Failed to improve writing. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!currentText.trim() || isLoading) return; // Prevent double-clicks
    
    // Use true original text if available, otherwise use immediate original or current text
    const textToSaveAsOriginal = trueOriginalText || originalText || currentText;
    
    setIsLoading(true);
    try {
      const response = await freeEntryAPI.save(textToSaveAsOriginal, currentText, language);
      
      if (response.success) {
        setSavedEntryId(response.entry_id);
        // Clear all text states after successful save to prevent duplicate saves
        setCurrentText('');
        setOriginalText('');
        setTrueOriginalText('');
        setTimeout(() => setSavedEntryId(null), 3000); // Hide success message after 3 seconds
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Failed to save entry. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    // Reset to the true original text that user first typed
    const textToResetTo = trueOriginalText || originalText;
    setCurrentText(textToResetTo);
    setOriginalText(''); // Clear intermediate original
    setTrueOriginalText(''); // Clear true original after reset
    setShowComparison(false);
    console.log('Resetting to true original text:', textToResetTo);
  };

  const handleDateSelect = async (date: string, entries: any[]) => {
    try {
      // If entries are already provided by the calendar, use them
      if (entries && entries.length > 0) {
        setSelectedDate(date);
        setSelectedDateSessions(entries);
        setShowHistoricalDiary(true);
      } else {
        // Fall back to fetching entries if not provided
        const response = await unifiedDiaryAPI.getByDate(date);
        if (response.success) {
          setSelectedDate(date);
          setSelectedDateSessions(response.entries);
          setShowHistoricalDiary(true);
        }
      }
    } catch (error) {
      console.error('Error loading diary for date:', error);
    }
  };

  const handleCloseHistorical = () => {
    setShowHistoricalDiary(false);
    setSelectedDate('');
    setSelectedDateSessions([]);
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
      setIsLoading(true);
      
      if (mode === 'casual' || mode === 'free_entry') {
        const numericId = parseInt(entryId.replace(`${mode}_`, ''));
        const response = await fetch(`http://localhost:8001/diary/entry/${numericId}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content: editingContent })
        });
        if (!response.ok) throw new Error('Failed to update entry');
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
      setIsLoading(false);
    }
  };

  const deleteEntry = async (entryId: string, mode: string) => {
    const confirmMessage = language === 'en' 
      ? 'Are you sure you want to delete this diary entry? This action cannot be undone.'
      : '确定要删除这个日记条目吗？此操作无法撤销。';
    
    if (!window.confirm(confirmMessage)) return;
    
    try {
      setIsLoading(true);
      
      if (mode === 'casual' || mode === 'free_entry') {
        const numericId = parseInt(entryId.replace(`${mode}_`, ''));
        const response = await fetch(`http://localhost:8001/diary/entry/${numericId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        if (!response.ok) throw new Error('Failed to delete entry');
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
      setIsLoading(false);
    }
  };

  const viewConversation = async (sessionId: string, mode: 'guided' | 'casual' = 'guided') => {
    try {
      setIsLoading(true);
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
      setIsLoading(false);
    }
  };

  // Note: Original text is now captured at the moment user clicks grammar/improvement buttons
  // This prevents issues with partial text capture during typing

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <Sidebar
        currentMode="free_entry"
        onSwitchToGuided={onSwitchToGuided}
        onSwitchToSimple={onSwitchToSimple}
      >
        {/* Calendar Section */}
        <div style={{ marginBottom: '20px' }}>
          <SimpleCalendar language={language} onDateSelect={handleDateSelect} />
        </div>

        {/* Action Buttons */}
        {currentText.trim() && (
          <div style={{ marginBottom: '20px' }}>
            <button
              onClick={handleCorrectGrammar}
              disabled={isLoading}
              style={{
                width: '100%',
                marginBottom: '8px',
                padding: '8px 16px',
                backgroundColor: isLoading ? '#ccc' : '#e8d5ff',
                color: isLoading ? '#666' : '#5b21b6',
                border: `2px solid ${isLoading ? '#ccc' : '#e8d5ff'}`,
                borderRadius: '5px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'normal',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = '#d4b8ff';
                  e.currentTarget.style.borderColor = '#d4b8ff';
                  e.currentTarget.style.color = 'white';
                }
              }}
              onMouseLeave={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = '#e8d5ff';
                  e.currentTarget.style.borderColor = '#e8d5ff';
                  e.currentTarget.style.color = '#5b21b6';
                }
              }}
            >
              {isLoading ? t.working : t.correctGrammar}
            </button>
            
            <button
              onClick={() => setShowImproveOptions(!showImproveOptions)}
              style={{
                width: '100%',
                marginBottom: '8px',
                padding: '8px 16px',
                backgroundColor: '#e8d5ff',
                color: '#5b21b6',
                border: '2px solid #e8d5ff',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'normal',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#d4b8ff';
                e.currentTarget.style.borderColor = '#d4b8ff';
                e.currentTarget.style.color = 'white';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#e8d5ff';
                e.currentTarget.style.borderColor = '#e8d5ff';
                e.currentTarget.style.color = '#5b21b6';
              }}
            >
              {showImproveOptions ? t.hideOptions : t.showOptions}
            </button>

            {/* Improvement Options */}
            {showImproveOptions && (
              <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <button
                    onClick={() => handleImproveWriting('general')}
                    disabled={isLoading}
                    style={{
                      width: '100%',
                      padding: '8px 16px',
                      backgroundColor: isLoading ? '#ccc' : '#e8d5ff',
                      color: isLoading ? '#666' : '#5b21b6',
                      border: `2px solid ${isLoading ? '#ccc' : '#e8d5ff'}`,
                      borderRadius: '5px',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: 'normal',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#d4b8ff';
                        e.currentTarget.style.borderColor = '#d4b8ff';
                        e.currentTarget.style.color = 'white';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#e8d5ff';
                        e.currentTarget.style.borderColor = '#e8d5ff';
                        e.currentTarget.style.color = '#5b21b6';
                      }
                    }}
                  >
                    {t.improveGeneral}
                  </button>
                  <button
                    onClick={() => handleImproveWriting('clarity')}
                    disabled={isLoading}
                    style={{
                      width: '100%',
                      padding: '8px 16px',
                      backgroundColor: isLoading ? '#ccc' : '#e8d5ff',
                      color: isLoading ? '#666' : '#5b21b6',
                      border: `2px solid ${isLoading ? '#ccc' : '#e8d5ff'}`,
                      borderRadius: '5px',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: 'normal',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#d4b8ff';
                        e.currentTarget.style.borderColor = '#d4b8ff';
                        e.currentTarget.style.color = 'white';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#e8d5ff';
                        e.currentTarget.style.borderColor = '#e8d5ff';
                        e.currentTarget.style.color = '#5b21b6';
                      }
                    }}
                  >
                    {t.improveClarity}
                  </button>
                  <button
                    onClick={() => handleImproveWriting('flow')}
                    disabled={isLoading}
                    style={{
                      width: '100%',
                      padding: '8px 16px',
                      backgroundColor: isLoading ? '#ccc' : '#e8d5ff',
                      color: isLoading ? '#666' : '#5b21b6',
                      border: `2px solid ${isLoading ? '#ccc' : '#e8d5ff'}`,
                      borderRadius: '5px',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: 'normal',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#d4b8ff';
                        e.currentTarget.style.borderColor = '#d4b8ff';
                        e.currentTarget.style.color = 'white';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#e8d5ff';
                        e.currentTarget.style.borderColor = '#e8d5ff';
                        e.currentTarget.style.color = '#5b21b6';
                      }
                    }}
                  >
                    {t.improveFlow}
                  </button>
                  <button
                    onClick={() => handleImproveWriting('vocabulary')}
                    disabled={isLoading}
                    style={{
                      width: '100%',
                      padding: '8px 16px',
                      backgroundColor: isLoading ? '#ccc' : '#e8d5ff',
                      color: isLoading ? '#666' : '#5b21b6',
                      border: `2px solid ${isLoading ? '#ccc' : '#e8d5ff'}`,
                      borderRadius: '5px',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: 'normal',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#d4b8ff';
                        e.currentTarget.style.borderColor = '#d4b8ff';
                        e.currentTarget.style.color = 'white';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.backgroundColor = '#e8d5ff';
                        e.currentTarget.style.borderColor = '#e8d5ff';
                        e.currentTarget.style.color = '#5b21b6';
                      }
                    }}
                  >
                    {t.improveVocabulary}
                  </button>
                </div>
              </div>
            )}

            {((originalText && originalText !== currentText) || (trueOriginalText && trueOriginalText !== currentText)) && (
              <>
                <button
                  onClick={() => setShowComparison(!showComparison)}
                  style={{
                    width: '100%',
                    marginBottom: '8px',
                    padding: '10px',
                    backgroundColor: '#17a2b8',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  {showComparison ? t.hideComparison : t.showComparison}
                </button>
                
                <button
                  onClick={handleReset}
                  style={{
                    width: '100%',
                    marginBottom: '8px',
                    padding: '10px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  {t.reset}
                </button>
              </>
            )}
            
            <button
              onClick={handleSave}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: isLoading ? '#ccc' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '16px',
                fontWeight: 'bold',
              }}
            >
              {isLoading ? t.working : t.save}
            </button>
          </div>
        )}

        {/* Success Message */}
        {savedEntryId && (
          <div style={{
            padding: '10px',
            backgroundColor: '#d4edda',
            border: '1px solid #c3e6cb',
            borderRadius: '5px',
            color: '#155724',
            fontSize: '14px',
          }}>
            ✅ {t.saved}
          </div>
        )}
      </Sidebar>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          backgroundColor: 'white',
          borderBottom: '1px solid #e0e0e0',
        }}>
          <div style={{ textAlign: 'center' }}>
            <h1 style={{ 
              margin: 0, 
              color: '#667eea', 
              fontWeight: '300'
            }}>
              Dear Me
            </h1>
            <p style={{ 
              margin: '2px 0 0 0', 
              color: '#999', 
              fontSize: '0.8rem', 
              fontStyle: 'italic'
            }}>
              Be Here, Be Now, Be You -- in a space you call your own
            </p>
            <div style={{ textAlign: 'left', marginTop: '15px' }}>
              <h2 style={{ 
                margin: '0', 
                fontSize: '14px', 
                color: '#333',
                fontWeight: 'normal'
              }}>
                {t.title}
              </h2>
              <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '12px', fontWeight: 'normal' }}>
                {t.subtitle}
              </p>
            </div>
          </div>
        </div>

        {/* Writing Area */}
        <div style={{ flex: 1, padding: '20px', backgroundColor: '#f8f9fa', position: 'relative' }}>
          <div style={{ height: '100%', position: 'relative' }}>
            <textarea
              value={currentText}
              onChange={(e) => setCurrentText(e.target.value)}
              placeholder={placeholders[language as keyof typeof placeholders]}
              disabled={isLoading}
              style={{
                width: '100%',
                height: '100%',
                padding: '20px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                backgroundColor: 'white',
                fontSize: '14px',
                lineHeight: '1.6',
                resize: 'none',
                outline: 'none',
                fontFamily: 'inherit',
              }}
            />
            
            {/* Word/Character Count */}
            <div style={{
              position: 'absolute',
              bottom: '25px',
              right: '25px',
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              padding: '5px 10px',
              borderRadius: '3px',
              fontSize: '12px',
              color: '#666',
            }}>
              {getWordCount(currentText)} {t.wordCount}
            </div>
          </div>
        </div>

        {/* Comparison View */}
        {showComparison && (originalText || trueOriginalText) && (() => {
          // Use true original if available, otherwise use immediate original
          const displayOriginalText = trueOriginalText || originalText;
          console.log('COMPARISON RENDER - displayOriginalText:', displayOriginalText);
          console.log('COMPARISON RENDER - currentText:', currentText);
          console.log('COMPARISON RENDER - trueOriginalText:', trueOriginalText);
          
          return displayOriginalText && displayOriginalText.trim() && displayOriginalText !== currentText ? (
          <div style={{
            padding: '20px',
            backgroundColor: '#e3f2fd',
            borderTop: '1px solid #e0e0e0',
          }}>
            <div style={{ display: 'flex', gap: '20px' }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ marginBottom: '10px', color: '#333', fontSize: '12px' }}>{t.originalVersion}</h3>
                <div style={{
                  padding: '15px',
                  backgroundColor: 'white',
                  borderRadius: '5px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                  color: '#666',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                  textAlign: 'left',
                  lineHeight: '1.4'
                }}>
                  {formatTextWithParagraphSpacing(displayOriginalText) || <span style={{color: '#ccc', fontStyle: 'italic'}}>No original text captured</span>}
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ marginBottom: '10px', color: '#333', fontSize: '16px' }}>{t.currentVersion}</h3>
                <div style={{
                  padding: '15px',
                  backgroundColor: 'white',
                  borderRadius: '5px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                  color: '#333',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                  textAlign: 'left',
                  lineHeight: '1.4'
                }}>
                  {formatTextWithParagraphSpacing(currentText)}
                </div>
              </div>
            </div>
          </div>
          ) : null;
        })()}

        {/* Historical Diary Modal */}
        <DiaryModal
          isOpen={showHistoricalDiary}
          onClose={handleCloseHistorical}
          selectedDate={selectedDate}
          entries={selectedDateSessions.map(entry => ({
            id: entry.id,
            content: entry.content,
            mode: entry.mode as 'guided' | 'casual' | 'free_entry',
            created_at: entry.created_at
          }))}
          language={language}
          editingEntryId={editingEntryId}
          editingContent={editingContent}
          loading={isLoading}
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
                          <div style={{ fontSize: '14px', lineHeight: '1.5' }}>
                            {message.content}
                          </div>
                          <div style={{
                            fontSize: '12px',
                            opacity: 0.7,
                            marginTop: '5px'
                          }}>
                            {new Date(message.created_at || '').toLocaleString()}
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
    </div>
  );
}