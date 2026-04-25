import React from 'react';
import { useTranslation } from 'react-i18next';
import { Video, Music, Settings, Info, Layers } from 'lucide-react';

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeView, onViewChange }) => {
  const { t } = useTranslation();

  const navItems = [
    { id: 'video', icon: <Video size={20} />, label: t('nav.video') },
    { id: 'audio', icon: <Music size={20} />, label: t('nav.audio') },
    { id: 'video_audio', icon: <Layers size={20} />, label: t('nav.video_audio') },
    { id: 'settings', icon: <Settings size={20} />, label: t('nav.settings') },
    { id: 'about', icon: <Info size={20} />, label: t('nav.about') },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>{t('app.title')}</h2>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeView === item.id ? 'active' : ''}`}
            onClick={() => onViewChange(item.id)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <p>{t('app.version', { version: '1.0.0' })}</p>
      </div>
    </aside>
  );
};

export default Sidebar;
