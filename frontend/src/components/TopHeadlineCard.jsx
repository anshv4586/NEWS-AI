import React, { useState } from 'react';
import { Star, Clock, ChevronDown, ChevronUp, Flame, ExternalLink, Sparkles } from 'lucide-react';

export default function TopHeadlineCard({ headlines = [], onCardClick }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const fallbackHeadlines = [
    {
      title: "Global markets rally as tech stocks lead strong gains",
      published_at: "Recently",
      url: "#",
      source: "Financial Times",
    },
  ];

  const items = headlines && headlines.length > 0 ? headlines : fallbackHeadlines;
  const top1 = items[0];
  const top10 = items.slice(0, 10);

  // Stock Market chart graphic default image
  const stockChartImg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120' fill='none'><rect width='120' height='120' rx='12' fill='%231b1d1f'/><path d='M20 90L45 70L70 80L100 35' stroke='%2322c55e' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/><path d='M85 35H100V50' stroke='%2322c55e' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/><path d='M20 90L45 70L70 80L100 35V90H20Z' fill='url(%23paint0_linear)' fill-opacity='0.2'/><defs><linearGradient id='paint0_linear' x1='60' y1='35' x2='60' y2='90' gradientUnits='userSpaceOnUse'><stop stop-color='%2322c55e'/><stop offset='1' stop-color='%2322c55e' stop-opacity='0'/></linearGradient></defs></svg>";

  return (
    <div className="top-headlines-section">
      {/* Featured #1 Headline Card */}
      <div
        className="top-headline-card glass-card clickable"
        onClick={() => onCardClick && onCardClick(top1)}
        title="Click to analyze with News AI"
      >
        <div className="headline-info">
          <div className="headline-badge">
            <Star size={14} className="star-icon" />
            <span>#1 Top World Headline</span>
          </div>

          <h3 className="headline-title">{top1.title}</h3>

          <div className="headline-meta">
            <Clock size={13} />
            <span>{top1.published_at || 'Recently'}</span>
            {top1.source && <span className="headline-source">• {top1.source}</span>}
          </div>
        </div>

        <div className="headline-thumbnail">
          <img src={stockChartImg} alt="Headline Graphic" />
        </div>
      </div>

      {/* Expand/Collapse Top 10 World Headlines Button */}
      <button
        className="toggle-top10-btn"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="toggle-btn-left">
          <Flame size={16} className="flame-icon" />
          <span>Top 10 World News Rankings (#1 to #10)</span>
        </div>
        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </button>

      {/* Top 10 Ranked Headlines Drawer / Accordion */}
      {isExpanded && (
        <div className="top10-list-container glass-card">
          <div className="top10-header-title">
            <Sparkles size={15} className="sparkle-gold" />
            <span>Click any headline to analyze with News AI:</span>
          </div>
          <div className="top10-items-grid">
            {top10.map((article, index) => {
              const rank = index + 1;
              return (
                <div
                  key={index}
                  className="top10-item-card"
                  onClick={() => onCardClick && onCardClick(article)}
                >
                  <div className={`rank-badge rank-${rank}`}>
                    #{rank}
                  </div>
                  <div className="top10-item-content">
                    <h4 className="top10-item-title">{article.title}</h4>
                    <div className="top10-item-meta">
                      <span className="top10-source">{article.source || 'News Source'}</span>
                      {article.published_at && (
                        <span className="top10-date">• {article.published_at}</span>
                      )}
                    </div>
                  </div>
                  <ExternalLink size={14} className="top10-link-icon" />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

