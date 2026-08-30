import React, { useState, useEffect } from 'react';
import { Newspaper, Sun, Moon, ChevronDown, Maximize2, Minimize2, Menu, User, LogOut, ShieldCheck } from 'lucide-react';

export default function Header({
  currentLang,
  onLangChange,
  theme,
  onThemeToggle,
  onOpenMobileDrawer,
  currentUser,
  onOpenAuth,
  onLogout,
}) {
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const languages = [
    { code: 'EN', name: 'English' },
    { code: 'HI', name: 'हिन्दी' },
    { code: 'HING', name: 'Hinglish' },
  ];

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch((err) => {
          console.error('Fullscreen toggle error:', err);
        });
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  return (
    <header className="app-header">
      <div className="header-brand">
        <button
          className="mobile-menu-btn"
          onClick={onOpenMobileDrawer}
          title="Open Navigation Menu"
        >
          <Menu size={20} />
        </button>

        <div className="logo-icon-wrapper">
          <Newspaper className="logo-icon" size={22} />
        </div>
        <div className="brand-text">
          <div className="brand-title-row">
            <span className="brand-name">News</span>
            <span className="brand-ai-badge">AI</span>
          </div>
          <p className="brand-subtitle">Your World, Simplified.</p>
        </div>
      </div>

      <div className="header-actions">
        {/* Language Selector Dropdown */}
        <div className="lang-select-container">
          <button 
            className="lang-pill-btn"
            onClick={() => setLangDropdownOpen(!langDropdownOpen)}
          >
            <span>{currentLang}</span>
            <ChevronDown size={14} className={`chevron-icon ${langDropdownOpen ? 'open' : ''}`} />
          </button>

          {langDropdownOpen && (
            <div className="lang-dropdown-menu">
              {languages.map((l) => (
                <button
                  key={l.code}
                  className={`lang-option ${currentLang === l.code ? 'active' : ''}`}
                  onClick={() => {
                    onLangChange(l.code);
                    setLangDropdownOpen(false);
                  }}
                >
                  {l.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Profile / Sign In Button */}
        {currentUser ? (
          <div className="user-profile-menu-container">
            <button
              className="user-profile-pill-btn"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              title={currentUser.email}
            >
              <div className="user-avatar-circle">
                {(currentUser.name || 'U').charAt(0).toUpperCase()}
              </div>
              <span className="user-display-name">
                {(currentUser.name || 'Client').split(' ')[0]}
              </span>
              <ChevronDown size={12} className={`chevron-icon ${userMenuOpen ? 'open' : ''}`} />
            </button>

            {userMenuOpen && (
              <div className="user-dropdown-card glass-card">
                <div className="user-dropdown-header">
                  <p className="user-full-name">{currentUser.name}</p>
                  <p className="user-email-text">{currentUser.email}</p>
                  <div className="user-client-badge">
                    <ShieldCheck size={12} />
                    <span>Client DB Verified</span>
                  </div>
                </div>
                <div className="user-dropdown-divider" />
                <button
                  className="user-dropdown-logout-btn"
                  onClick={() => {
                    setUserMenuOpen(false);
                    onLogout && onLogout();
                  }}
                >
                  <LogOut size={14} />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            className="header-signin-btn"
            onClick={onOpenAuth}
            title="Sign in or Register account"
          >
            <User size={15} />
            <span>Sign In</span>
          </button>
        )}

        {/* Fullscreen Toggle Button */}
        <button
          className="fullscreen-toggle-btn"
          onClick={toggleFullscreen}
          title={isFullscreen ? 'Exit Full Screen' : 'Enter Full Screen'}
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          <span className="btn-fullscreen-label">{isFullscreen ? 'Exit Full' : 'Full Screen'}</span>
        </button>

        {/* Theme Toggle Button */}
        <button 
          className="theme-toggle-btn" 
          onClick={onThemeToggle}
          title="Toggle Theme"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </div>
    </header>
  );
}

