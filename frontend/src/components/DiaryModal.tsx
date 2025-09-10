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
  
  // Look for existing paragraph breaks first
  if (text.includes('\n\n')) {
    return text; // Text already has proper paragraph formatting
  }
  
  // Enhanced paragraph detection for better readability
  let formattedText = text
    // Break before temporal transitions
    .replace(/ (After|Later|During|Throughout|In the evening|In the morning|This morning|This afternoon|Tonight|Yesterday|Tomorrow|Before|Following|Subsequently)/gi, '\n\n$1')
    // Break before reflection and emotional statements
    .replace(/ (As I reflect|Looking back|What struck me|I realize|I noticed|I felt|I think|I believe|I hope|I'm grateful|I appreciate|It warmed|It made me)/gi, '\n\n$1')
    // Break before conclusions and summaries
    .replace(/ (Overall|In conclusion|To sum up|All in all|Most importantly|What matters|The key thing|Above all)/gi, '\n\n$1')
    // Break before contrasting thoughts
    .replace(/ (However|Although|Despite|On the other hand|But|Yet|Nevertheless|Still|Even though)/gi, '\n\n$1')
    // Break at natural topic shifts (sentence patterns that indicate new topics)
    .replace(/\. ([A-Z][^.]*(?:day|morning|afternoon|evening|experience|moment|time|conversation|thought|feeling|memory))/g, '.\n\n$1')
    // Break before gratitude and hope expressions
    .replace(/ (I'm thankful|I'm grateful|I'm blessed|I'm hopeful|I wish|I dream|I aspire|Looking forward)/gi, '\n\n$1')
    // Break at emotional transitions
    .replace(/ (The more|What surprised me|What touched me|What moved me|What I learned|What became clear)/gi, '\n\n$1')
    // Chinese paragraph markers
    .replace(/ (后来|接着|然后|回想起来|我觉得|我想|我希望|我感谢|总的来说|最重要的是)/gi, '\n\n$1')
    // Clean up any triple newlines
    .replace(/\n\n\n+/g, '\n\n')
    // Trim any leading/trailing whitespace
    .trim();
  
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
                    padding: '15px',
                    backgroundColor: '#f8f9fa',
                    border: '1px solid #e9ecef',
                    borderRadius: '8px',
                    marginBottom: '15px',
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.4',
                    textAlign: 'left'
                  }}>
                    {formatTextWithParagraphSpacing(getEntryContent(entry))}
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