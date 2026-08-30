import React, { useState } from 'react';
import { X, Lock, Mail, User, Globe, ArrowRight, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { registerUser, loginUser } from '../services/api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [country, setCountry] = useState('India');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const resetForm = () => {
    setError(null);
    setSuccessMsg(null);
  };

  const handleModeSwitch = (newMode) => {
    setMode(newMode);
    resetForm();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      if (mode === 'register') {
        const res = await registerUser({
          name,
          email,
          password,
          country,
        });
        setSuccessMsg('Account registered in client_db successfully!');
        if (res.client) {
          localStorage.setItem('news_ai_user', JSON.stringify(res.client));
          if (res.token) localStorage.setItem('news_ai_token', res.token);
          setTimeout(() => {
            onAuthSuccess && onAuthSuccess(res.client);
            onClose();
          }, 800);
        }
      } else {
        const res = await loginUser({
          email,
          password,
        });
        setSuccessMsg('Welcome back!');
        if (res.client) {
          localStorage.setItem('news_ai_user', JSON.stringify(res.client));
          if (res.token) localStorage.setItem('news_ai_token', res.token);
          setTimeout(() => {
            onAuthSuccess && onAuthSuccess(res.client);
            onClose();
          }, 600);
        }
      }
    } catch (err) {
      setError(err.message || 'Authentication error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal-card glass-card" onClick={(e) => e.stopPropagation()}>
        {/* Close Button */}
        <button className="auth-modal-close-btn" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div className="auth-modal-header">
          <div className="auth-modal-icon-badge">
            <Lock size={22} className="auth-icon-glow" />
          </div>
          <h2 className="auth-modal-title">
            {mode === 'login' ? 'Sign In to News AI' : 'Create Client Account'}
          </h2>
          <p className="auth-modal-subtitle">
            {mode === 'login'
              ? 'Access real-time breaking news tailored to your preferences.'
              : 'Join as a registered client and sync your saved news and search history.'}
          </p>
        </div>

        {/* Mode Switch Tabs */}
        <div className="auth-tab-group">
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => handleModeSwitch('login')}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => handleModeSwitch('register')}
          >
            Sign Up
          </button>
        </div>

        {/* Error / Success Notifications */}
        {error && (
          <div className="auth-alert error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="auth-alert success">
            <CheckCircle size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Auth Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="auth-input-group">
              <label className="auth-label">Full Name</label>
              <div className="auth-input-wrapper">
                <User size={18} className="auth-field-icon" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Rahul Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="auth-input"
                />
              </div>
            </div>
          )}

          <div className="auth-input-group">
            <label className="auth-label">Email Address</label>
            <div className="auth-input-wrapper">
              <Mail size={18} className="auth-field-icon" />
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
              />
            </div>
          </div>

          <div className="auth-input-group">
            <label className="auth-label">Password</label>
            <div className="auth-input-wrapper">
              <Lock size={18} className="auth-field-icon" />
              <input
                type="password"
                required
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
              />
            </div>
          </div>

          {mode === 'register' && (
            <div className="auth-input-group">
              <label className="auth-label">Preferred Region / Country</label>
              <div className="auth-input-wrapper">
                <Globe size={18} className="auth-field-icon" />
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="auth-input auth-select"
                >
                  <option value="India">India</option>
                  <option value="USA">United States</option>
                  <option value="UK">United Kingdom</option>
                  <option value="Global">Global / International</option>
                  <option value="Europe">Europe</option>
                  <option value="Canada">Canada</option>
                  <option value="Australia">Australia</option>
                </select>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="auth-submit-btn"
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="spin-animation" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <span>{mode === 'login' ? 'Sign In' : 'Register Account'}</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Footer switch prompt */}
        <div className="auth-footer-prompt">
          {mode === 'login' ? (
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                className="auth-link-inline"
                onClick={() => handleModeSwitch('register')}
              >
                Create one now
              </button>
            </p>
          ) : (
            <p>
              Already registered?{' '}
              <button
                type="button"
                className="auth-link-inline"
                onClick={() => handleModeSwitch('login')}
              >
                Sign in here
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
