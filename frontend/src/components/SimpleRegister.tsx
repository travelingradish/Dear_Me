import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';

const SimpleRegister: React.FC = () => {
  const [username, setUsername] = useState('');
  const [age, setAge] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    // Age is optional, but if provided, it should be valid
    let ageNum: number | null = null;
    if (age.trim()) {
      ageNum = parseInt(age);
      if (isNaN(ageNum) || ageNum < 8 || ageNum > 120) {
        setError('If you provide an age, it must be between 8 and 120');
        return;
      }
    }

    setLoading(true);

    try {
      await register(username, ageNum, password);
      navigate('/');
    } catch (err: any) {
      console.error('Registration error:', err);
      let errorMessage = 'Registration failed';
      
      try {
        if (err.response?.data?.detail) {
          const detail = err.response.data.detail;
          
          if (typeof detail === 'string') {
            errorMessage = detail;
          } else if (Array.isArray(detail)) {
            const firstError = detail[0];
            if (firstError && typeof firstError === 'object' && firstError.msg) {
              errorMessage = firstError.msg;
            } else if (typeof firstError === 'string') {
              errorMessage = firstError;
            }
          } else if (typeof detail === 'object' && detail.msg) {
            errorMessage = detail.msg;
          }
        } else if (err.message) {
          errorMessage = err.message;
        }
      } catch (parseError) {
        console.error('Error parsing error message:', parseError);
        errorMessage = 'Registration failed due to an unexpected error';
      }
      
      setError(typeof errorMessage === 'string' ? errorMessage : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const registerStyle: React.CSSProperties = {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #28a745 0%, #667eea 100%)',
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
    background: 'linear-gradient(135deg, #28a745 0%, #667eea 100%)',
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
    <div style={registerStyle}>
      <div style={cardStyle}>
        <h1 style={titleStyle}>Dear Me</h1>
        <p style={{ textAlign: 'center', color: '#888', fontSize: '0.9rem', marginBottom: '10px', fontStyle: 'italic' }}>
          Be Here, Be Now, Be You
        </p>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>
          Create your personal reflection space
        </p>

        {error && <div style={errorStyle}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={inputStyle}
              placeholder="Choose a username"
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Age (optional)
            </label>
            <input
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              style={inputStyle}
              placeholder="Enter your age (optional)"
              min="8"
              max="120"
            />
            <p style={{ fontSize: '11px', color: '#666', marginTop: '4px', fontStyle: 'italic' }}>
              Providing your age helps us personalize conversations for your life stage
            </p>
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
              placeholder="Create a password"
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              style={inputStyle}
              placeholder="Confirm your password"
              required
            />
          </div>

          <button type="submit" disabled={loading} style={buttonStyle}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <p style={{ color: '#666' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#28a745', textDecoration: 'none', fontWeight: '500' }}>
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SimpleRegister;