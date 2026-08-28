import React, { useState, useEffect } from 'react';
import { Newspaper, Sun, Moon, ChevronDown, Maximize2, Minimize2, Menu } from 'lucide-react';

export default function Header({ currentLang, onLangChange, theme, onThemeToggle, onOpenMobileDrawer }) {
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
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

