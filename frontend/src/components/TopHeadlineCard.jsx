import React, { useState } from 'react';
import { Sparkles, ChevronRight } from 'lucide-react';

export default function TopHeadlineCard({ headlines = [], onCardClick }) {
  const [showAll, setShowAll] = useState(false);

  const fallbackHeadlines = [
    {
      title: "Global markets respond positively to inflation easing in major economies",
      published_at: "1h ago",
      url: "#",
      source: "Reuters",
      thumb: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100' height='100' fill='%231e293b'/><circle cx='50' cy='50' r='30' fill='%233b82f6'/></svg>"
    },
    {
      title: "India's growth forecast remains strong amid global uncertainties",
      published_at: "2h ago",
      url: "#",
      source: "The Hindu",
      thumb: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100' height='100' fill='%231e293b'/><rect y='30' width='100' height='40' fill='%23f97316'/></svg>"
    },
    {
      title: "New AI model outperforms previous benchmarks in reasoning tasks",
      published_at: "3h ago",
      url: "#",
      source: "TechCrunch",
      thumb: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100' height='100' fill='%231e293b'/><path d='M30 50L50 30L70 50L50 70Z' fill='%236366f1'/></svg>"
    },
  ];

  const items = headlines && headlines.length > 0 ? headlines : fallbackHeadlines;
  const displayItems = showAll ? items.slice(0, 10) : items.slice(0, 3);

  // Default thumbnail fallback generator
  const getThumb = (item, index) => {
    if (item.thumb) return item.thumb;
    const colors = ['#1d2438', '#231d38', '#1d382d'];
    const icons = ['#6366f1', '#3b82f6', '#10b981'];
    const bg = colors[index % colors.length];
    const fg = icons[index % icons.length];
    return `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100' height='100' rx='10' fill='${encodeURIComponent(bg)}'/><circle cx='50' cy='50' r='24' fill='${encodeURIComponent(fg)}' opacity='0.7'/></svg>`;
  };

  return (
    <div className="top-headlines-card-container glass-card">
      {/* Header Row */}
      <div className="card-header-row">
        <div className="card-header-title">
          <Sparkles size={16} className="sparkle-purple-icon" />
          <span>Top Headlines</span>
        </div>

        <button
          className="view-all-link"
          onClick={() => setShowAll(!showAll)}
        >
          <span>{showAll ? 'Show less' : 'View all'}</span>
          <ChevronRight size={14} />
        </button>
      </div>

      {/* Headline Items List */}
      <div className="headlines-items-list">
        {displayItems.map((article, index) => (
          <div
            key={index}
            className="headline-list-item"
            onClick={() => onCardClick && onCardClick(article)}
          >
            <div className="item-thumb-wrapper">
              <img src={getThumb(article, index)} alt="News Thumbnail" />
            </div>

            <div className="item-content-block">
              <h4 className="item-news-title">{article.title}</h4>
              <div className="item-news-meta">
                <span>{article.source || 'News Source'}</span>
                <span>•</span>
                <span>{article.published_at || 'Recently'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

