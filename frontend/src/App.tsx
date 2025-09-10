import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext.tsx';
import SimpleProtectedRoute from './components/SimpleProtectedRoute.tsx';
import SimpleLogin from './components/SimpleLogin.tsx';
import SimpleRegister from './components/SimpleRegister.tsx';
import Home from './components/Home.tsx';
import MainChat from './components/MainChat.tsx';
import LanguageToggle from './components/LanguageToggle.tsx';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <LanguageToggle />
          <Routes>
            <Route path="/login" element={<SimpleLogin />} />
            <Route path="/register" element={<SimpleRegister />} />
            <Route 
              path="/" 
              element={
                <SimpleProtectedRoute>
                  <Home />
                </SimpleProtectedRoute>
              } 
            />
            <Route 
              path="/chat" 
              element={
                <SimpleProtectedRoute>
                  <MainChat />
                </SimpleProtectedRoute>
              } 
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
