import React, { useState, useEffect } from 'react';
import SimpleChat from './SimpleChat.tsx';
import GuidedChat from './GuidedChat.tsx';
import FreeEntry from './FreeEntry.tsx';

type ChatMode = 'guided' | 'simple' | 'free';

const MainChat: React.FC = () => {
  const [chatMode, setChatMode] = useState<ChatMode>(() => {
    // Check localStorage for user preference, default to guided mode
    const saved = localStorage.getItem('chatMode');
    return (saved as ChatMode) || 'guided';
  });


  useEffect(() => {
    // Save preference to localStorage
    localStorage.setItem('chatMode', chatMode);
  }, [chatMode]);

  const switchToGuided = () => {
    setChatMode('guided');
  };

  const switchToLegacy = () => {
    setChatMode('simple');
  };

  const switchToFreeEntry = () => {
    setChatMode('free');
  };

  if (chatMode === 'guided') {
    return <GuidedChat onSwitchToLegacy={switchToLegacy} onSwitchToFreeEntry={switchToFreeEntry} />;
  } else if (chatMode === 'simple') {
    return <SimpleChat onSwitchToGuided={switchToGuided} onSwitchToFreeEntry={switchToFreeEntry} />;
  } else {
    return <FreeEntry onSwitchToGuided={switchToGuided} onSwitchToSimple={switchToLegacy} />;
  }
};

export default MainChat;