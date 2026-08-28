import React from 'react';
import { History, Bookmark, Settings } from 'lucide-react';

export default function BottomNav({ activeTab, onSelectTab, savedCount = 0 }) {
  return (
    <div className="bottom-nav-container">
      <div className="bottom-nav-bar glass-card">
        <button
          className={`nav-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => onSelectTab('history')}
        >
          <History size={18} />
          <span>History</span>
        </button>

        <div className="nav-divider"></div>

        <button
          className={`nav-tab-btn ${activeTab === 'saved' ? 'active' : ''}`}
          onClick={() => onSelectTab('saved')}
        >
          <div className="tab-icon-wrapper">
            <Bookmark size={18} />
            {savedCount > 0 && <span className="saved-count-badge">{savedCount}</span>}
          </div>
          <span>Saved</span>
        </button>

        <div className="nav-divider"></div>

        <button
          className={`nav-tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => onSelectTab('settings')}
        >
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>
    </div>
  );
}
