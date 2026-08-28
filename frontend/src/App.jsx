import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import HeroWelcome from './components/HeroWelcome';
import TopHeadlineCard from './components/TopHeadlineCard';
import CategoryPills from './components/CategoryPills';
import ChatSection from './components/ChatSection';
import BottomNav from './components/BottomNav';
import { HistoryModal, SavedModal, SettingsModal } from './components/Modals';
import AuthModal from './components/AuthModal';
import { History, Bookmark, Trash2, ExternalLink, Sparkles } from 'lucide-react';

import {
  sendChatMessage,
  fetchLatestNews,
  fetchNewsByCategory,
  sendVoiceChat,
  fetchChatSessions,
  fetchCurrentUser,
  logoutUser,
  fetchUserSavedArticles,
  saveUserArticle,
  removeUserArticle,
} from './services/api';

import './App.css';

export default function App() {
  const [currentLang, setCurrentLang] = useState('EN');
  const [theme, setTheme] = useState('dark');
  const [queryCount, setQueryCount] = useState(2);
  const [topHeadlines, setTopHeadlines] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // User Auth State
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authPromptMsg, setAuthPromptMsg] = useState('');

  // Bookmarks
  const [savedArticles, setSavedArticles] = useState(() => {
    try {
      const stored = localStorage.getItem('news_ai_saved');
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      return [];
    }
  });

  // Modal tab states: null | 'history' | 'saved' | 'settings'
  const [activeModal, setActiveModal] = useState(null);
  const [chatSessions, setChatSessions] = useState([]);

  // Check user session & load initial data on mount
  useEffect(() => {
    async function loadInitialData() {
      // 1. Check user session
      const authRes = await fetchCurrentUser();
      if (authRes.authenticated && authRes.user) {
        setCurrentUser(authRes.user);
        const userSaved = await fetchUserSavedArticles();
        if (userSaved && userSaved.length > 0) {
          setSavedArticles(userSaved);
        }
      }

      // 2. Fetch top headlines
      const articles = await fetchLatestNews(10);
      if (articles && articles.length > 0) {
        setTopHeadlines(articles);
      }

      // 3. Fetch chat history sessions
      const sessions = await fetchChatSessions();
      if (sessions) {
        setChatSessions(sessions);
      }
    }
    loadInitialData();
  }, []);

  // Save articles to local storage backup
  useEffect(() => {
    localStorage.setItem('news_ai_saved', JSON.stringify(savedArticles));
  }, [savedArticles]);

  // Sync body class for global theme background
  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  const handleLangChange = (langCode) => {
    setCurrentLang(langCode);
  };

  const handleThemeToggle = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };


  // Stay Informed Button Click
  const handleStayInformedClick = () => {
    handleSendMessage("Summarize today's top world news and breaking headlines.");
  };

  // Category selection handler
  const handleSelectCategory = async (categoryName) => {
    setSelectedCategory(categoryName);
    handleSendMessage(`What are the latest updates in ${categoryName} news today?`);
  };

  // Submit Text Query
  const handleSendMessage = async (userText) => {
    if (!userText || isLoading) return;

    // Add user message to UI
    const updatedMessages = [...messages, { role: 'user', content: userText }];
    setMessages(updatedMessages);
    setIsLoading(true);
    setQueryCount((prev) => prev + 1);

    try {
      const langParam = currentLang === 'HI' ? 'Hindi' : currentLang === 'HING' ? 'Hinglish' : 'English';
      const res = await sendChatMessage(userText, conversationId, langParam);

      if (res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          content: res.answer,
          sources: res.sources || [],
        },
      ]);

      // Refresh chat sessions list
      const updatedSessions = await fetchChatSessions();
      if (updatedSessions) setChatSessions(updatedSessions);
    } catch (err) {
      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          content: `⚠️ ${err.message || 'Unable to connect to News AI backend. Please ensure backend is running.'}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Voice Recording Submit
  const handleVoiceInput = async (audioBlob) => {
    setIsLoading(true);
    try {
      const langParam = currentLang === 'HI' ? 'Hindi' : currentLang === 'HING' ? 'Hinglish' : 'English';
      const res = await sendVoiceChat(audioBlob, conversationId, langParam);

      if (res.conversation_id) setConversationId(res.conversation_id);

      const userQuery = res.user_message || '🎙️ Voice Query';
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: userQuery },
        {
          role: 'assistant',
          content: res.answer,
          sources: res.sources || [],
          audioB64: res.audio_base64,
        },
      ]);
      setQueryCount((prev) => prev + 1);
    } catch (err) {
      alert('Voice query processing error.');
    } finally {
      setIsLoading(false);
    }
  };

  // Quick Action: Hindi Prompt
  const handleHindiPrompt = () => {
    setCurrentLang('HI');
    handleSendMessage('आज की मुख्य समाचार क्या हैं?');
  };

  // Quick Action: Summarize
  const handleSummarize = () => {
    handleSendMessage('Summarize the top global news stories from the last 24 hours into key bullet points.');
  };

  // Save / Bookmark Article
  const handleSaveArticle = async (article) => {
    if (!currentUser) {
      setAuthPromptMsg('Please sign in to save news articles to your account.');
      setIsAuthModalOpen(true);
      return;
    }

    if (savedArticles.some((a) => a.url === article.url)) {
      setSavedArticles(savedArticles.filter((a) => a.url !== article.url));
      await removeUserArticle(article.url);
    } else {
      setSavedArticles([...savedArticles, article]);
      await saveUserArticle(article);
    }
  };

  const handleRemoveSaved = async (url) => {
    setSavedArticles(savedArticles.filter((a) => a.url !== url));
    if (currentUser) {
      await removeUserArticle(url);
    }
  };

  const handleLogout = async () => {
    await logoutUser();
    setCurrentUser(null);
    setSavedArticles([]);
    setActiveModal(null);
  };

  // Bottom Navigation Tab Trigger
  const handleSelectTab = async (tabName) => {
    if (tabName === 'saved' && !currentUser) {
      setAuthPromptMsg('Please sign in to view your saved articles.');
      setActiveModal('settings');
      return;
    }

    if (tabName === 'history') {
      const sessions = await fetchChatSessions();
      setChatSessions(sessions);
    }
    setActiveModal(tabName);
  };

  const savedUrls = savedArticles.map((a) => a.url);

  return (
    <div className={`app-container ${theme}`}>
      {/* Header */}
      <Header
        currentLang={currentLang}
        onLangChange={handleLangChange}
        theme={theme}
        onThemeToggle={handleThemeToggle}
      />

      {/* Main Responsive Grid Layout */}
      <div className="app-main-layout">
        <div className="main-content-column">
          {/* Hero Welcome */}
          <HeroWelcome
            onStayInformedClick={handleStayInformedClick}
          />

          {/* Top Headline Card & Top 10 World Headlines Selector */}
          <TopHeadlineCard
            headlines={topHeadlines}
            onCardClick={(item) => handleSendMessage(`Tell me more details about: ${item.title}`)}
          />

          {/* Categories Selector */}
          <CategoryPills
            selectedCategory={selectedCategory}
            onSelectCategory={handleSelectCategory}
          />

          {/* Chat Section & Quick Action Pills */}
          <ChatSection
            messages={messages}
            onSendMessage={handleSendMessage}
            onVoiceInput={handleVoiceInput}
            onHindiPrompt={handleHindiPrompt}
            onSummarize={handleSummarize}
            isLoading={isLoading}
            onSaveArticle={handleSaveArticle}
            savedUrls={savedUrls}
          />
        </div>

        {/* Desktop Sidebar Panel (visible on full screen / widescreen) */}
        <aside className="desktop-sidebar-panel">
          <div className="sidebar-widget glass-card">
            <div className="widget-header">
              <History size={16} className="widget-icon" />
              <span>Recent Conversations</span>
            </div>
            {chatSessions && chatSessions.length > 0 ? (
              <div className="widget-session-list">
                {chatSessions.slice(0, 6).map((session) => (
                  <div
                    key={session.id}
                    className="widget-session-item"
                    onClick={() => setConversationId(session.id)}
                  >
                    <span className="session-title">{session.title || 'Conversation'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="widget-empty">No previous sessions</p>
            )}
          </div>

          <div className="sidebar-widget glass-card">
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
                      onClick={() => handleRemoveSaved(article.url)}
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
        </aside>
      </div>

      {/* Fixed Bottom Navigation Bar */}
      <BottomNav
        activeTab={activeModal}
        onSelectTab={handleSelectTab}
        savedCount={savedArticles.length}
      />

      {/* Interactive Overlay Modals */}
      <HistoryModal
        isOpen={activeModal === 'history'}
        onClose={() => setActiveModal(null)}
        sessions={chatSessions}
        onSelectSession={(id) => {
          setConversationId(id);
          setActiveModal(null);
        }}
      />

      <SavedModal
        isOpen={activeModal === 'saved'}
        onClose={() => setActiveModal(null)}
        savedArticles={savedArticles}
        onRemoveArticle={handleRemoveSaved}
      />

      <SettingsModal
        isOpen={activeModal === 'settings'}
        onClose={() => setActiveModal(null)}
        currentLang={currentLang}
        onLangChange={handleLangChange}
        currentUser={currentUser}
        onOpenAuthModal={() => {
          setActiveModal(null);
          setIsAuthModalOpen(true);
        }}
        onLogout={handleLogout}
      />

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => {
          setIsAuthModalOpen(false);
          setAuthPromptMsg('');
        }}
        promptMessage={authPromptMsg}
        onAuthSuccess={async (user) => {
          setCurrentUser(user);
          setAuthPromptMsg('');
          const userSaved = await fetchUserSavedArticles();
          if (userSaved) setSavedArticles(userSaved);
        }}
      />
    </div>
  );
}
