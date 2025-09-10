import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, language } = useAuth();

  const handleStartJournaling = () => {
    navigate('/chat');
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Translation objects
  const translations = {
    en: {
      welcome: 'Welcome',
      logout: 'Logout',
      title: 'Dear Me',
      subtitle: 'Be Here, Be Now, Be You',
      subtitleSecond: '— in a space you call your own',
      bannerFirst: 'A new day. A deep breath. A space to reflect.',
      bannerSecond: 'Gentle care for your mind.',
      startButton: 'Start Unpacking',
      features: [
        { icon: '💭', title: 'Guided Reflection', desc: 'Thoughtful prompts to guide your daily check-in' },
        { icon: '📖', title: 'Personal Journal', desc: 'AI-crafted entries from your own words' },
        { icon: '🌱', title: 'Mindful Growth', desc: 'Track your journey of self-discovery' }
      ]
    },
    zh: {
      welcome: '欢迎',
      logout: '登出',
      title: 'Dear Me',
      subtitle: '此时，此刻，做自己',
      subtitleSecond: '— 在属于你的空间里',
      bannerFirst: '凝神， 静思，梳理，释放。从容前行。',
      bannerSecond: '',
      startButton: '开始记录',
      features: [
        { icon: '💭', title: '引导反思', desc: '贴心的提示引导你的每日思考' },
        { icon: '📖', title: '个人日记', desc: '用AI将你的话语编织成日记' },
        { icon: '🌱', title: '心灵成长', desc: '记录你的自我发现之旅' }
      ]
    }
  };

  const t = translations[language as keyof typeof translations] || translations.en;

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      fontFamily: '"Inter", "Segoe UI", system-ui, sans-serif'
    }}>
      {/* Header with user info and logout */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '15px',
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: '14px'
      }}>
        <span>{t.welcome}, {user?.username}</span>
        <button
          onClick={handleLogout}
          style={{
            background: 'rgba(255, 255, 255, 0.2)',
            border: 'none',
            borderRadius: '20px',
            padding: '8px 16px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px',
            transition: 'all 0.3s ease'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
          }}
        >
          {t.logout}
        </button>
      </div>

      {/* Main content */}
      <div style={{
        textAlign: 'center',
        maxWidth: '600px',
        animation: 'fadeInUp 1s ease-out'
      }}>
        {/* App title */}
        <h1 style={{
          fontSize: '4rem',
          fontWeight: '300',
          color: 'white',
          marginBottom: '10px',
          letterSpacing: '2px',
          textShadow: '0 2px 20px rgba(0,0,0,0.1)'
        }}>
          {t.title}
        </h1>

        {/* Subtitle */}
        <p style={{
          fontSize: '1.2rem',
          color: 'rgba(255, 255, 255, 0.8)',
          marginBottom: '40px',
          fontWeight: '300',
          letterSpacing: '0.5px',
          lineHeight: '1.6'
        }}>
          {t.subtitle}<br />
          <span style={{ fontSize: '1rem', opacity: 0.7 }}>
            {t.subtitleSecond}
          </span>
        </p>

        {/* Inspirational quote */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.1)',
          borderRadius: '20px',
          padding: '30px',
          marginBottom: '40px',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          <p style={{
            fontSize: '1.1rem',
            color: 'rgba(255, 255, 255, 0.9)',
            fontStyle: 'italic',
            margin: '0',
            lineHeight: '1.7'
          }}>
            {t.bannerFirst}
          </p>
          <p style={{
            fontSize: '1.1rem',
            color: 'rgba(255, 255, 255, 0.9)',
            fontStyle: 'italic',
            margin: '0',
            lineHeight: '1.7'
          }}>
            {t.bannerSecond}
          </p>
        </div>

        {/* Call to action */}
        <button
          onClick={handleStartJournaling}
          style={{
            background: 'rgba(255, 255, 255, 0.9)',
            border: 'none',
            borderRadius: '50px',
            padding: '18px 40px',
            fontSize: '1.1rem',
            fontWeight: '500',
            color: '#667eea',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
            letterSpacing: '0.5px'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 15px 40px rgba(0,0,0,0.3)';
            e.currentTarget.style.background = 'white';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 10px 30px rgba(0,0,0,0.2)';
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.9)';
          }}
        >
          {t.startButton}
        </button>

        {/* Features */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '40px',
          marginTop: '60px',
          flexWrap: 'wrap'
        }}>
          {t.features.map((feature, index) => (
            <div
              key={index}
              style={{
                textAlign: 'center',
                maxWidth: '150px',
                opacity: 0.8
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>
                {feature.icon}
              </div>
              <h3 style={{
                color: 'white',
                fontSize: '0.9rem',
                fontWeight: '500',
                marginBottom: '8px'
              }}>
                {feature.title}
              </h3>
              <p style={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.8rem',
                lineHeight: '1.4',
                margin: 0
              }}>
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Floating elements for ambiance */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '10%',
        width: '100px',
        height: '100px',
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.1)',
        animation: 'float 6s ease-in-out infinite'
      }} />
      
      <div style={{
        position: 'absolute',
        bottom: '15%',
        right: '15%',
        width: '60px',
        height: '60px',
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.05)',
        animation: 'float 8s ease-in-out infinite reverse'
      }} />

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }
      `}</style>
    </div>
  );
};

export default Home;