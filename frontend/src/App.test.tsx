import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app with login when not authenticated', () => {
  render(<App />);
  // Since app shows login form by default, test for login-related elements
  const appElement = screen.getByText(/Dear Me/i);
  expect(appElement).toBeInTheDocument();
  
  const loginButton = screen.getByText(/Sign In/i);
  expect(loginButton).toBeInTheDocument();
});
