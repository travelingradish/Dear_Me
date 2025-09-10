import React from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';

const LanguageToggle: React.FC = () => {
  const { language, setLanguage } = useAuth();

  const toggleLanguage = () => {
    const newLanguage = language === 'en' ? 'zh' : 'en';
    setLanguage(newLanguage);
  };

  return (
    <button
      onClick={toggleLanguage}
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 1000,
        padding: '8px 12px',
        backgroundColor: '#8b5cf6',
        color: 'white',
        border: 'none',
        borderRadius: '20px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        boxShadow: '0 2px 10px rgba(139, 92, 246, 0.3)',
        transition: 'all 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#7c3aed';
        e.currentTarget.style.transform = 'scale(1.05)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = '#8b5cf6';
        e.currentTarget.style.transform = 'scale(1)';
      }}
      title={language === 'en' ? 'Switch to Chinese' : 'Switch to English'}
    >
      🌐 {language === 'en' ? 'Eng/中文' : '中文/Eng'}
    </button>
  );
};

export default LanguageToggle;