import React from 'react';
import { Newspaper, Sparkles } from 'lucide-react';

export default function HeroWelcome({ onStayInformedClick }) {
  return (
    <div className="hero-welcome-container">
      {/* Sparkle Decorations */}
      <div className="sparkle sparkle-left">
        <Sparkles size={16} />
      </div>
      <div className="sparkle sparkle-right">
        <Sparkles size={16} />
      </div>

      {/* Wireframe Globe Background Overlay */}
      <div className="globe-wireframe-svg">
        <svg viewBox="0 0 300 300" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="150" cy="150" r="130" stroke="rgba(255, 255, 255, 0.07)" strokeWidth="1.5" strokeDasharray="4 4" />
          <circle cx="150" cy="150" r="95" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
          <ellipse cx="150" cy="150" rx="130" ry="50" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
          <ellipse cx="150" cy="150" rx="60" ry="130" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
          <line x1="20" y1="150" x2="280" y2="150" stroke="rgba(255, 255, 255, 0.06)" strokeWidth="1" />
          <line x1="150" y1="20" x2="150" y2="280" stroke="rgba(255, 255, 255, 0.06)" strokeWidth="1" />
        </svg>
      </div>

      <div className="hero-content">
        <h1 className="hero-title">Welcome</h1>
        <p className="hero-subtitle">Ask anything about world & state news</p>

        <div className="hero-action-block">
          <button className="btn-stay-informed" onClick={onStayInformedClick}>
            <Newspaper size={18} />
            <span>Stay Informed</span>
          </button>
        </div>
      </div>
    </div>
  );
}

