import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import SkipLink from './components/Accessibility/SkipLink';
import ThemeProvider from './theme/ThemeProvider';
import { useTheme } from './theme';

// Lazy load pages for better performance
import HomePage from './pages/Home';
import AgentsPage from './pages/Agents';
import AgentDetailPage from './pages/AgentDetail';
import SettingsPage from './pages/Settings';
import NotFoundPage from './pages/NotFound';

function App() {
  const { theme } = useTheme();
  
  // Apply theme class to html element
  useEffect(() => {
    const html = document.documentElement;
    if (theme === 'dark') {
      html.classList.add('dark');
      html.classList.remove('light');
    } else if (theme === 'light') {
      html.classList.remove('dark');
      html.classList.add('light');
    }
  }, [theme]);

  return (
    <ThemeProvider>
      {/* Skip Link for Accessibility (US-061) */}
      <SkipLink />
      
      {/* Main App Content */}
      <div className="min-h-screen bg-surface text-text-primary transition-colors duration-300">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/agents/:id" element={<AgentDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/404" element={<NotFoundPage />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </div>
    </ThemeProvider>
  );
}

export default App;
