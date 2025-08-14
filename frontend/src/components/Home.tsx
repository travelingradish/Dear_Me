import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleStartJournaling = () => {
    navigate('/chat');
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

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
        right: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '15px',
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: '14px'
      }}>
        <span>Welcome, {user?.username}</span>
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
          Logout
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
          Dear Me
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
          Be Here, Be Now, Be You<br />
          <span style={{ fontSize: '1rem', opacity: 0.7 }}>
            — in a space you call your own
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
            "Each day is a new beginning. Take a deep breath, reflect on your journey, 
            and let your thoughts flow freely in this sacred space of self-discovery."
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
          Start Your Daily Reflection
        </button>

        {/* Features */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '40px',
          marginTop: '60px',
          flexWrap: 'wrap'
        }}>
          {[
            { icon: '💭', title: 'Guided Reflection', desc: 'Thoughtful prompts to guide your daily check-in' },
            { icon: '📖', title: 'Personal Journal', desc: 'AI-crafted entries from your own words' },
            { icon: '🌱', title: 'Mindful Growth', desc: 'Track your journey of self-discovery' }
          ].map((feature, index) => (
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