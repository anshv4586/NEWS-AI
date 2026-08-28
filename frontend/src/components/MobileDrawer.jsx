import React from 'react';
import { X, History, Bookmark, Trash2, ExternalLink } from 'lucide-react';

export default function MobileDrawer({
  isOpen,
  onClose,
  chatSessions = [],
  savedArticles = [],
  onSelectSession,
  onRemoveSaved,
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop mobile-drawer-backdrop" onClick={onClose}>
      <div className="mobile-drawer-content glass-card" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="mobile-drawer-header">
          <span className="drawer-title">Navigation Drawer</span>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="mobile-drawer-body">
          {/* Recent Conversations Widget */}
          <div className="sidebar-widget">
            <div className="widget-header">
              <History size={16} className="widget-icon" />
              <span>Recent Conversations</span>
            </div>
            {chatSessions && chatSessions.length > 0 ? (
              <div className="widget-session-list">
                {chatSessions.slice(0, 8).map((session) => (
                  <div
                    key={session.id}
                    className="widget-session-item"
                    onClick={() => {
                      onSelectSession(session.id);
                      onClose();
                    }}
                  >
                    <span className="session-title">{session.title || 'Conversation'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="widget-empty">No previous sessions</p>
            )}
          </div>

          {/* Saved Bookmarks Widget */}
          <div className="sidebar-widget">
            <div className="widget-header">
              <Bookmark size={16} className="widget-icon" />
              <span>Saved Bookmarks ({savedArticles.length})</span>
            </div>
            {savedArticles && savedArticles.length > 0 ? (
              <div className="widget-saved-list">
                {savedArticles.map((article, i) => (
                  <div key={i} className="widget-saved-item">
                    <a href={article.url} target="_blank" rel="noopener noreferrer" className="saved-link">
                      {article.title}
                    </a>
                    <button
                      className="remove-btn"
                      onClick={() => onRemoveSaved(article.url)}
                      title="Remove Bookmark"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="widget-empty">No saved articles yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
