import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MessageSquare, FileText, ShieldCheck, Volume2, Bookmark, Check, Sparkles, ExternalLink } from 'lucide-react';

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
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

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

  // Browser Speech Recording for Voice Input
  const handleMicClick = async () => {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        audioChunksRef.current = [];

        mediaRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };

        mediaRecorderRef.current.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          onVoiceInput(audioBlob);
          stream.getTracks().forEach((track) => track.stop());
        };

        mediaRecorderRef.current.start();
        setIsRecording(true);
      } catch (err) {
        alert('Microphone access unavailable or denied.');
      }
    }
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

      {/* Main Dark Input Box matching user's design image */}
      <div className="chat-input-container glass-card">
        <textarea
          className="chat-textarea"
          placeholder="Ask News AI anything..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
        />

        <div className="input-bottom-row">
          <button
            className={`btn-send-circle ${inputText.trim() ? 'active' : ''}`}
            onClick={handleSend}
            disabled={!inputText.trim() || isLoading}
          >
            <Send size={16} />
          </button>
        </div>
      </div>

      {/* Quick Action Pills Row matching user's design */}
      <div className="quick-actions-row">
        <button className={`action-pill ${isRecording ? 'recording' : ''}`} onClick={handleMicClick}>
          <Mic size={15} />
          <span>{isRecording ? 'Listening...' : 'Voice Input'}</span>
        </button>

        <button className="action-pill" onClick={onHindiPrompt}>
          <MessageSquare size={15} />
          <span>हिन्दी में पूछें</span>
        </button>

        <button className="action-pill" onClick={onSummarize}>
          <FileText size={15} />
          <span>Summarize</span>
        </button>
      </div>

      {/* Trust Subtext Badge matching user's design */}
      <div className="trust-disclaimer-badge">
        <ShieldCheck size={15} />
        <span>News is AI-generated from trusted sources.</span>
      </div>
    </div>
  );
}
