import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';
import '../styles/responsive.css';

interface SidebarProps {
  currentMode: 'guided' | 'casual' | 'free_entry';
  onSwitchToGuided?: () => void;
  onSwitchToSimple?: () => void;
  onSwitchToFreeEntry?: () => void;
  children?: React.ReactNode; // For mode-specific content like calendar
}

export default function Sidebar({
  currentMode,
  onSwitchToGuided,
  onSwitchToSimple,
  onSwitchToFreeEntry,
  children
}: SidebarProps) {
  const { user, logout, updateCharacterName, language } = useAuth();
  const [showCharacterNamingModal, setShowCharacterNamingModal] = useState(false);
  const [characterName, setCharacterName] = useState('');
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const handleUpdateCharacterName = async () => {
    if (!characterName.trim()) return;
    
    try {
      await updateCharacterName(characterName.trim());
      setShowCharacterNamingModal(false);
      setCharacterName('');
    } catch (error) {
      console.error('Error updating character name:', error);
      alert(language === 'en' ? 'Failed to update character name' : '更新角色名称失败');
    }
  };

  const getModeDisplayName = (mode: string) => {
    switch (mode) {
      case 'guided':
        return { icon: '📝', name: language === 'en' ? 'Guided Mode' : '引导模式' };
      case 'casual':
        return { icon: '💬', name: language === 'en' ? 'Casual Mode' : '休闲模式' };
      case 'free_entry':
        return { icon: '✍️', name: language === 'en' ? 'Free Entry Mode' : '自由书写模式' };
      default:
        return { icon: '', name: '' };
    }
  };

  const renderModeButton = (mode: 'guided' | 'casual' | 'free_entry', onClick?: () => void) => {
    const isCurrentMode = mode === currentMode;
    const { icon, name } = getModeDisplayName(mode);
    
    // Use filled lighter purple for inactive buttons
    const lightPurpleFilled = '#e8d5ff';  // Light purple background for inactive
    const darkPurple = '#8b5cf6';         // Dark purple for current mode
    const hoverPurple = '#d4b8ff';        // Slightly darker purple for hover

    return (
      <button
        key={mode}
        onClick={onClick}
        disabled={isCurrentMode}
        style={{
          padding: '8px 16px',
          backgroundColor: isCurrentMode ? darkPurple : lightPurpleFilled,
          color: isCurrentMode ? 'white' : '#5b21b6',  // Dark purple text for inactive
          border: `2px solid ${isCurrentMode ? darkPurple : lightPurpleFilled}`,
          borderRadius: '5px',
          cursor: isCurrentMode ? 'default' : 'pointer',
          fontSize: '14px',
          fontWeight: isCurrentMode ? 'bold' : 'normal',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          if (!isCurrentMode) {
            e.currentTarget.style.backgroundColor = hoverPurple;
            e.currentTarget.style.borderColor = hoverPurple;
            e.currentTarget.style.color = 'white';
          }
        }}
        onMouseLeave={(e) => {
          if (!isCurrentMode) {
            e.currentTarget.style.backgroundColor = lightPurpleFilled;
            e.currentTarget.style.borderColor = lightPurpleFilled;
            e.currentTarget.style.color = '#5b21b6';
          }
        }}
      >
        {icon} {name} {isCurrentMode ? (language === 'en' ? '(Current)' : '(当前)') : ''}
      </button>
    );
  };

  return (
    <>
      {/* Hamburger button — only visible on mobile via CSS */}
      <button
        className="hamburger-btn"
        onClick={() => setIsMobileOpen(true)}
        aria-label="Open menu"
      >
        ☰
      </button>

      {/* Overlay — only visible on mobile when open */}
      {isMobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar panel */}
      <div className={`sidebar ${isMobileOpen ? 'mobile-open' : ''}`}>
      {/* User Info Section */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '10px', color: '#333' }}>Welcome, {user?.username}!</h3>
        <p style={{ color: '#666', fontSize: '14px' }}>{user?.email}</p>
        <p style={{ color: '#667eea', fontSize: '13px', marginTop: '8px' }}>
          AI Assistant: {user?.ai_character_name}
        </p>
        <button
          onClick={() => {
            setCharacterName(user?.ai_character_name || '');
            setShowCharacterNamingModal(true);
          }}
          style={{
            marginTop: '8px',
            marginRight: '10px',
            padding: '6px 12px',
            backgroundColor: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          {language === 'en' ? 'Rename AI' : '重命名AI'}
        </button>
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
        
        {/* Mode Selection Buttons */}
        <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {renderModeButton('guided', onSwitchToGuided)}
          {renderModeButton('casual', onSwitchToSimple)}
          {renderModeButton('free_entry', onSwitchToFreeEntry)}
        </div>
      </div>



      {/* Mode-specific content (calendar, etc.) */}
      {children}

      {/* Character Naming Modal */}
      {showCharacterNamingModal && (
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
            padding: '30px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
          }}>
            <h3 style={{ 
              marginBottom: '20px', 
              color: '#333',
              textAlign: 'center',
              fontSize: '20px'
            }}>
              {language === 'en' ? 'Name Your AI Friend' : '为你的AI朋友命名'}
            </h3>
            <p style={{ 
              color: '#666', 
              marginBottom: '20px', 
              textAlign: 'center',
              fontSize: '14px'
            }}>
              {language === 'en' 
                ? 'Give your AI companion a personal name to make your conversations more meaningful!' 
                : '为你的AI伴侣起一个个人名字，让对话更有意义！'}
            </p>
            <input
              type="text"
              value={characterName}
              onChange={(e) => setCharacterName(e.target.value)}
              placeholder={language === 'en' ? 'Enter character name...' : '输入角色名称...'}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #e0e0e0',
                borderRadius: '8px',
                fontSize: '16px',
                marginBottom: '20px',
                boxSizing: 'border-box',
                outline: 'none'
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleUpdateCharacterName();
                }
              }}
              autoFocus
            />
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowCharacterNamingModal(false);
                  setCharacterName('');
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                {language === 'en' ? 'Cancel' : '取消'}
              </button>
              <button
                onClick={handleUpdateCharacterName}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                {language === 'en' ? 'Save' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
      </div>

      {/* Mobile bottom navigation */}
      <nav className="mobile-bottom-nav">
        <button
          className={`mobile-nav-btn ${currentMode === 'guided' ? 'active' : ''}`}
          onClick={() => { onSwitchToGuided?.(); setIsMobileOpen(false); }}
          aria-label={language === 'en' ? 'Guided mode' : '引导模式'}
        >
          <span>📝</span>
          <span>{language === 'en' ? 'Guided' : '引导'}</span>
        </button>
        <button
          className={`mobile-nav-btn ${currentMode === 'casual' ? 'active' : ''}`}
          onClick={() => { onSwitchToSimple?.(); setIsMobileOpen(false); }}
          aria-label={language === 'en' ? 'Casual mode' : '休闲模式'}
        >
          <span>💬</span>
          <span>{language === 'en' ? 'Casual' : '休闲'}</span>
        </button>
        <button
          className={`mobile-nav-btn ${currentMode === 'free_entry' ? 'active' : ''}`}
          onClick={() => { onSwitchToFreeEntry?.(); setIsMobileOpen(false); }}
          aria-label={language === 'en' ? 'Free entry mode' : '自由书写模式'}
        >
          <span>✍️</span>
          <span>{language === 'en' ? 'Free' : '自由'}</span>
        </button>
      </nav>
    </>
  );
}