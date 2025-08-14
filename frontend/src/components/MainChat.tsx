import React, { useState, useEffect } from 'react';
import SimpleChat from './SimpleChat.tsx';
import GuidedChat from './GuidedChat.tsx';

const MainChat: React.FC = () => {
  const [useGuidedMode, setUseGuidedMode] = useState(() => {
    // Check localStorage for user preference, default to guided mode
    const saved = localStorage.getItem('useGuidedMode');
    return saved !== null ? JSON.parse(saved) : true;
  });

  useEffect(() => {
    // Save preference to localStorage
    localStorage.setItem('useGuidedMode', JSON.stringify(useGuidedMode));
  }, [useGuidedMode]);

  const switchToGuided = () => {
    setUseGuidedMode(true);
  };

  const switchToLegacy = () => {
    setUseGuidedMode(false);
  };

  if (useGuidedMode) {
    return <GuidedChat onSwitchToLegacy={switchToLegacy} />;
  } else {
    return <SimpleChat onSwitchToGuided={switchToGuided} />;
  }
};

export default MainChat;