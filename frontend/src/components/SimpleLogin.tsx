import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';

const SimpleLogin: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const loginStyle: React.CSSProperties = {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
  };

  const cardStyle: React.CSSProperties = {
    background: 'white',
    borderRadius: '20px',
    boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
    padding: '40px',
    width: '100%',
    maxWidth: '400px',
  };

  const titleStyle: React.CSSProperties = {
    textAlign: 'center',
    marginBottom: '30px',
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#333',
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '12px 16px',
    border: '2px solid #e0e0e0',
    borderRadius: '10px',
    fontSize: '16px',
    outline: 'none',
    transition: 'border-color 0.3s ease',
    marginBottom: '20px',
  };

  const buttonStyle: React.CSSProperties = {
    width: '100%',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '12px',
    borderRadius: '10px',
    border: 'none',
    fontSize: '16px',
    fontWeight: '600',
    cursor: loading ? 'not-allowed' : 'pointer',
    opacity: loading ? 0.6 : 1,
  };

  const errorStyle: React.CSSProperties = {
    background: '#fef2f2',
    border: '1px solid #fecaca',
    color: '#b91c1c',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '20px',
  };

  return (
    <div style={loginStyle}>
      <div style={cardStyle}>
        <h1 style={titleStyle}>Dear Me</h1>
        <p style={{ textAlign: 'center', color: '#888', fontSize: '0.9rem', marginBottom: '10px', fontStyle: 'italic' }}>
          Be Here, Be Now, Be You
        </p>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>
          Welcome back to your personal reflection space
        </p>

        {error && <div style={errorStyle}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputStyle}
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={inputStyle}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" disabled={loading} style={buttonStyle}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <p style={{ color: '#666' }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#667eea', textDecoration: 'none', fontWeight: '500' }}>
              Create one here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SimpleLogin;