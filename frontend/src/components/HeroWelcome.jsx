import React from 'react';
import { Globe } from 'lucide-react';

export default function HeroWelcome({ onStayInformedClick }) {
  return (
    <div className="hero-welcome-container">
      {/* Central Glowing Indigo Globe Icon */}
      <div className="hero-globe-icon-wrapper">
        <Globe size={44} className="hero-globe-icon" />
      </div>

      <div className="hero-content">
        <h1 className="hero-title">
          Welcome to <span className="title-highlight">News AI</span>
        </h1>
        <p className="hero-subtitle">Your intelligent news companion</p>
        <div className="hero-tagline-row">
          <span>Stay updated</span> • <span>Ask anything</span> • <span>Get clarity</span>
        </div>
      </div>
    </div>
  );
}

