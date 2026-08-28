import React from 'react';
import { TrendingUp, Globe, Landmark, Briefcase, Cpu, Heart, Trophy, Film, Leaf } from 'lucide-react';

export default function CategoryPills({ selectedCategory, onSelectCategory }) {
  const categories = [
    { id: null, label: 'Top Headlines', icon: TrendingUp },
    { id: 'World', label: 'World', icon: Globe },
    { id: 'India', label: 'India', icon: Landmark },
    { id: 'Business', label: 'Business', icon: Briefcase },
    { id: 'Tech', label: 'Tech', icon: Cpu },
    { id: 'Health', label: 'Health', icon: Heart },
    { id: 'Sports', label: 'Sports', icon: Trophy },
    { id: 'Entertainment', label: 'Entertainment', icon: Film },
    { id: 'Climate', label: 'Climate', icon: Leaf },
  ];

  return (
    <div className="categories-section">
      <div className="categories-scroll-wrapper">
        {categories.map((cat) => {
          const IconComponent = cat.icon;
          const isSelected = selectedCategory === cat.id;

          return (
            <button
              key={cat.label}
              className={`category-pill ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectCategory(cat.id)}
            >
              <IconComponent size={15} />
              <span>{cat.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
