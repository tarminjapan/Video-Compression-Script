import React from 'react';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
  activeView: string;
  onViewChange: (view: string) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, activeView, onViewChange }) => {
  return (
    <div className="app-container">
      <Sidebar activeView={activeView} onViewChange={onViewChange} />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout;
