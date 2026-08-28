import React from 'react';
import { X, History, Bookmark, Settings, ExternalLink, Trash2, Globe, Cpu, User, LogOut, Lock, ShieldCheck } from 'lucide-react';

export function HistoryModal({ isOpen, onClose, sessions = [], onSelectSession, onDeleteSession }) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <History size={18} className="gold-text" />
            <span>Chat History</span>
          </div>
          <button className="close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="modal-body">
          {sessions.length === 0 ? (
            <div className="empty-state">No past chat sessions found.</div>
          ) : (
            <div className="session-list">
              {sessions.map((s) => (
                <div key={s.id} className="session-item" onClick={() => onSelectSession(s.id)}>
                  <div className="session-info">
                    <div className="session-title">{s.title || 'Chat Session'}</div>
                    <div className="session-meta">{s.turn_count || 1} turns • {s.language}</div>
                  </div>
                  {onDeleteSession && (
                    <button
                      className="delete-session-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(s.id);
                      }}
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function SavedModal({ isOpen, onClose, savedArticles = [], onRemoveArticle }) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <Bookmark size={18} className="gold-text" />
            <span>Saved News Articles ({savedArticles.length})</span>
          </div>
          <button className="close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="modal-body">
          {savedArticles.length === 0 ? (
            <div className="empty-state">No saved news articles yet. Click the bookmark icon on any source card to save it.</div>
          ) : (
            <div className="saved-article-list">
              {savedArticles.map((art, idx) => (
                <div key={idx} className="saved-article-card">
                  <div className="saved-article-info">
                    <a href={art.url} target="_blank" rel="noopener noreferrer" className="saved-title-link">
                      {art.title}
                    </a>
                    <div className="saved-source-tag">{art.source}</div>
                  </div>
                  <div className="saved-actions">
                    <a href={art.url} target="_blank" rel="noopener noreferrer" className="icon-link">
                      <ExternalLink size={16} />
                    </a>
                    <button className="remove-saved-btn" onClick={() => onRemoveArticle(art.url)}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function SettingsModal({
  isOpen,
  onClose,
  currentLang,
  onLangChange,
  currentUser,
  onOpenAuthModal,
  onLogout,
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <Settings size={18} className="gold-text" />
            <span>Application Settings</span>
          </div>
          <button className="close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="modal-body">
          {/* Account Section at Top */}
          <div className="settings-section account-section">
            <label className="settings-label">
              <User size={16} />
              <span>Account</span>
            </label>
            
            {currentUser ? (
              <div className="logged-in-user-card">
                <div className="user-info-row">
                  <ShieldCheck size={18} className="verified-icon" />
                  <div className="user-details">
                    <span className="user-identifier">
                      {currentUser.email || currentUser.phone || 'Verified User'}
                    </span>
                    <span className="verified-tag">✓ Verified Account</span>
                  </div>
                </div>
                <button className="logout-btn" onClick={onLogout}>
                  <LogOut size={14} />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="logged-out-user-card">
                <p className="login-prompt-text">Sign in to save articles and sync your news preferences.</p>
                <button className="btn-gold-pill login-btn-pill" onClick={onOpenAuthModal}>
                  <Lock size={14} />
                  <span>Login or Sign Up</span>
                </button>
              </div>
            )}
          </div>

          <div className="settings-section">
            <label className="settings-label">
              <Globe size={16} />
              <span>Target Language Mode</span>
            </label>
            <select
              value={currentLang}
              onChange={(e) => onLangChange(e.target.value)}
              className="settings-select"
            >
              <option value="EN">English</option>
              <option value="HI">हिन्दी (Hindi)</option>
              <option value="HING">Hinglish</option>
            </select>
          </div>



          <div className="settings-footer">
            <span>Global News AI v1.0 • Grounded RAG News Companion</span>
          </div>
        </div>
      </div>
    </div>
  );
}

