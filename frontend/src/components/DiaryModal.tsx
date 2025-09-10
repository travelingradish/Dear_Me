import React from 'react';

interface DiaryEntry {
  id: string;
  content: string;
  mode: 'guided' | 'casual' | 'free_entry';
  created_at?: string;
  final_diary?: string; // For guided mode entries
}

interface DiaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDate: string;
  entries: DiaryEntry[];
  language: string;
  editingEntryId: string | null;
  editingContent: string;
  loading: boolean;
  onStartEditing: (entryId: string, content: string) => void;
  onCancelEditing: () => void;
  onSaveEdit: (entryId: string, mode: string) => void;
  onDeleteEntry?: (entryId: string, mode: string) => void;
  onViewConversation?: (sessionId: string, mode: 'guided' | 'casual') => void;
  setEditingContent: (content: string) => void;
}

// Helper function for paragraph spacing (shared across all modes)
const formatTextWithParagraphSpacing = (text: string) => {
  if (!text) return text;
  
  // Clean up the text first
  let formattedText = text.trim();
  
  // If text already has proper paragraph breaks (double newlines), return as is
  if (formattedText.includes('\n\n')) {
    // Clean up any excessive spacing and return
    return formattedText
      .replace(/\n\n\n+/g, '\n\n')
      .replace(/\n\s+\n/g, '\n\n')
      .trim();
  }
  
  // Check if text has single newlines that might indicate paragraph structure
  if (formattedText.includes('\n') && !formattedText.includes('\n\n')) {
    // Convert single newlines to double newlines for proper paragraph display
    return formattedText
      .replace(/\n/g, '\n\n')
      .replace(/\n\n\n+/g, '\n\n')
      .trim();
  }
  
  // Only apply aggressive formatting to text that appears to be truly unformatted
  // (single long paragraph with no line breaks at all)
  if (!formattedText.includes('\n')) {
    // Very conservative paragraph detection - only break at major transitions
    formattedText = formattedText
      // Break before clear temporal transitions
      .replace(/ (After wrapping up|Later that day|In the evening|During the morning|Throughout the day|Yesterday|Tomorrow|This morning|This afternoon|Tonight)/gi, '\n\n$1')
      // Break before major reflection statements
      .replace(/ (As I reflect on|Looking back on|What struck me most|I realize now that|What I learned today)/gi, '\n\n$1')
      // Break before major conclusions
      .replace(/ (Overall|In conclusion|Most importantly|What matters most|Above all else)/gi, '\n\n$1')
      // Break before strong contrasts
      .replace(/ (However|Nevertheless|On the other hand|Despite this)/gi, '\n\n$1')
      // Chinese major transitions
      .replace(/ (总的来说|最重要的是|然而|不过|回想起来)/gi, '\n\n$1')
      // Clean up excessive spacing
      .replace(/\n\n\n+/g, '\n\n')
      .trim();
    
    // Only if we still have no paragraph breaks AND text is very long, group sentences
    if (!formattedText.includes('\n\n') && formattedText.length > 300) {
      const sentences = formattedText.split(/[.!?。！？]\s+/);
      if (sentences.length > 4) {
        // Group sentences into paragraphs of 3-4 sentences each
        const paragraphs = [];
        for (let i = 0; i < sentences.length; i += 3) {
          const paragraph = sentences.slice(i, i + 3).join('. ');
          if (paragraph.trim()) {
            paragraphs.push(paragraph.trim());
          }
        }
        formattedText = paragraphs.join('\n\n');
      }
    }
  }
  
  return formattedText;
};

const DiaryModal: React.FC<DiaryModalProps> = ({
  isOpen,
  onClose,
  selectedDate,
  entries,
  language,
  editingEntryId,
  editingContent,
  loading,
  onStartEditing,
  onCancelEditing,
  onSaveEdit,
  onDeleteEntry,
  onViewConversation,
  setEditingContent,
}) => {
  if (!isOpen) return null;

  const getModeDisplayName = (mode: string) => {
    switch (mode) {
      case 'guided':
        return language === 'en' ? '📝 Guided Mode' : '📝 引导模式';
      case 'free_entry':
        return language === 'en' ? '✍️ Free Entry Mode' : '✍️ 自由书写模式';
      default: // casual
        return language === 'en' ? '💬 Casual Mode' : '💬 休闲模式';
    }
  };

  const getModeBackgroundColor = (mode: string) => {
    switch (mode) {
      case 'guided':
        return '#e3f2fd';
      case 'free_entry':
        return '#fff3e0';
      default: // casual
        return '#f3e5f5';
    }
  };

  const getEntryContent = (entry: DiaryEntry) => {
    // For guided mode, use final_diary if available, otherwise use content
    return entry.final_diary || entry.content;
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        width: '90%',
        maxWidth: '800px',
        maxHeight: '80%',
        padding: '30px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
      }}>
        {/* Modal Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}>
          <h2 style={{ margin: 0, fontSize: '24px', color: '#333', fontWeight: '600' }}>
            {language === 'en' ? `Diary for ${selectedDate}` : `${selectedDate} 的日记`}
          </h2>
          <button
            onClick={onClose}
            style={{
              backgroundColor: '#dc3545',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px',
              cursor: 'pointer',
              color: 'white',
              padding: '6px 12px',
              fontWeight: '500',
            }}
          >
            ×
          </button>
        </div>

        {/* Entries List */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto'
        }}>
          {entries.map((entry, index) => (
            <div key={entry.id || index}>
              {/* Mode indicator */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '15px'
              }}>
                <div style={{
                  fontSize: '14px',
                  color: '#666',
                  backgroundColor: getModeBackgroundColor(entry.mode),
                  padding: '6px 12px',
                  borderRadius: '16px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}>
                  {getModeDisplayName(entry.mode)}
                </div>
              </div>

              {/* Entry content */}
              {editingEntryId === entry.id ? (
                <div style={{ marginBottom: '15px' }}>
                  <textarea
                    value={editingContent}
                    onChange={(e) => setEditingContent(e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: '200px',
                      padding: '15px',
                      border: '2px solid #007bff',
                      borderRadius: '8px',
                      fontSize: '14px',
                      lineHeight: '1.4',
                      resize: 'vertical',
                      fontFamily: 'inherit',
                      outline: 'none',
                    }}
                    placeholder={language === 'en' ? 'Edit your diary...' : '编辑你的日记...'}
                  />
                  <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => onSaveEdit(entry.id, entry.mode)}
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
                      onClick={onCancelEditing}
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
                <>
                  <div style={{
                    padding: '20px',
                    backgroundColor: '#f8f9fa',
                    border: '1px solid #e9ecef',
                    borderRadius: '8px',
                    marginBottom: '15px',
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.6',
                    textAlign: 'left',
                    fontSize: '15px',
                    color: '#333',
                    fontFamily: 'system-ui, -apple-system, sans-serif',
                    letterSpacing: '0.01em'
                  }} 
                  className="diary-content"
                  dangerouslySetInnerHTML={{
                    __html: formatTextWithParagraphSpacing(getEntryContent(entry))
                      .split('\n\n')
                      .map(paragraph => `<p style="margin: 0 0 1em 0; line-height: 1.6;">${paragraph}</p>`)
                      .join('')
                  }}>
                  </div>

                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
                    <button
                      onClick={() => onStartEditing(entry.id, getEntryContent(entry))}
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
                      {language === 'en' ? '✏️ Edit' : '✏️ 编辑'}
                    </button>
                    {onDeleteEntry && (
                      <button
                        onClick={() => onDeleteEntry(entry.id, entry.mode)}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#dc3545',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer'
                        }}
                      >
                        {language === 'en' ? '🗑️ Delete' : '🗑️ 删除'}
                      </button>
                    )}
                    {onViewConversation && entry.mode !== 'free_entry' && (
                      <button
                        onClick={() => onViewConversation(entry.id, entry.mode === 'guided' ? 'guided' : 'casual')}
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
                    )}
                  </div>

                  {/* Created timestamp */}
                  {entry.created_at && (
                    <div style={{
                      fontSize: '12px',
                      color: '#999',
                      textAlign: 'center',
                      marginTop: '10px',
                      paddingTop: '10px',
                      borderTop: '1px solid #f0f0f0'
                    }}>
                      Created: {new Date(entry.created_at).toLocaleString()}
                    </div>
                  )}
                </>
              )}

              {/* Separator between entries if multiple */}
              {index < entries.length - 1 && (
                <hr style={{ 
                  margin: '30px 0', 
                  border: 'none', 
                  borderTop: '2px solid #f0f0f0' 
                }} />
              )}
            </div>
          ))}

          {entries.length === 0 && (
            <div style={{
              textAlign: 'center',
              color: '#666',
              padding: '40px',
              fontSize: '16px'
            }}>
              {language === 'en' ? 'No diary entries found for this date.' : '这个日期没有找到日记条目。'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DiaryModal;