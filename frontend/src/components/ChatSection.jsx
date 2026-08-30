import React, { useState } from 'react';
import { Send, Sparkles, Volume2, Bookmark, Check, ExternalLink } from 'lucide-react';

export default function ChatSection({
  messages,
  onSendMessage,
  onVoiceInput,
  onHindiPrompt,
  onSummarize,
  isLoading,
  onSaveArticle,
  savedUrls = [],
}) {
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Quick prompt chip click
  const handleChipClick = (promptText) => {
    onSendMessage(promptText);
  };

  return (
    <div className="chat-section-wrapper">
      {/* Active Conversation Messages View (if any) */}
      {messages && messages.length > 0 && (
        <div className="messages-history-container">
          {messages.map((msg, index) => (
            <div key={index} className={`message-bubble-wrapper ${msg.role}`}>
              <div className="message-header">
                {msg.role === 'user' ? (
                  <span className="user-label">You</span>
                ) : (
                  <div className="ai-label-row">
                    <Sparkles size={14} className="ai-sparkle-icon" />
                    <span>News AI</span>
                  </div>
                )}
              </div>

              <div className="message-body">{msg.content}</div>

              {/* Sources Grounding List */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-card-list">
                  <div className="sources-header">Grounded Sources:</div>
                  <div className="sources-grid">
                    {msg.sources.map((src, idx) => {
                      const isSaved = savedUrls.includes(src.url);
                      return (
                        <div key={idx} className="source-item-chip">
                          <a href={src.url} target="_blank" rel="noopener noreferrer" className="source-link">
                            <ExternalLink size={12} />
                            <span className="source-title">{src.title}</span>
                            <span className="source-publisher">({src.source})</span>
                          </a>
                          <button
                            className={`save-btn ${isSaved ? 'saved' : ''}`}
                            onClick={() => onSaveArticle(src)}
                            title={isSaved ? 'Saved' : 'Save Article'}
                          >
                            {isSaved ? <Check size={12} /> : <Bookmark size={12} />}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* TTS Audio Player if available */}
              {msg.audioB64 && (
                <div className="audio-player-row">
                  <Volume2 size={16} />
                  <audio controls autoPlay src={`data:audio/mp3;base64,${msg.audioB64}`} className="custom-audio" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="message-bubble-wrapper assistant loading">
              <div className="ai-label-row">
                <Sparkles size={14} className="ai-sparkle-icon spinning" />
                <span>Searching live global news sources...</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Dark Input Box matching exact user screenshot */}
      <div className="chat-input-container glass-card">
        <textarea
          className="chat-textarea"
          placeholder="Ask anything about the news..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
        />

        <div className="input-bottom-actions-row">
          <button
            className={`btn-send-circle-indigo ${inputText.trim() ? 'active' : ''}`}
            onClick={handleSend}
            disabled={!inputText.trim() || isLoading}
            title="Send Message"
          >
            <Send size={16} />
          </button>
        </div>
      </div>

      {/* Quick Suggestion Prompt Chips matching exact screenshot */}
      <div className="quick-prompt-chips-scroll">
        <button className="prompt-chip" onClick={() => handleChipClick("Tell me the latest world news headlines")}>
          Latest world news
        </button>
        <button className="prompt-chip" onClick={() => handleChipClick("What is happening in India today?")}>
          News from India
        </button>
        <button className="prompt-chip" onClick={() => handleChipClick("Show me top business & stock updates")}>
          Business updates
        </button>
        <button className="prompt-chip" onClick={() => handleChipClick("What are the latest technology AI news?")}>
          Tech news
        </button>
      </div>
    </div>
  );
}
