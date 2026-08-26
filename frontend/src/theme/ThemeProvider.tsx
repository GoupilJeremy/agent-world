/**
 * Agent World - Theme Provider
 * Fournisseur de contexte pour la gestion des thèmes
 * Conforme aux exigences US-063 : Thème personnalisable
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Theme, ThemeContextType, ThemeConfig, CustomThemeColors } from './types';
import { lightTheme } from './light';
import { darkTheme } from './dark';

// Available themes
const availableThemes: ThemeConfig[] = [lightTheme, darkTheme];

// Default context value
const defaultContext: ThemeContextType = {
  theme: 'light',
  setTheme: () => {},
  customColors: null,
  setCustomColors: () => {},
  themes: availableThemes,
};

// Create theme context
const ThemeContext = createContext<ThemeContextType>(defaultContext);

// Get initial theme from localStorage or system preference
const getInitialTheme = (): Theme => {
  const savedTheme = localStorage.getItem('agent-world-theme') as Theme | null;
  if (savedTheme && ['light', 'dark', 'custom'].includes(savedTheme)) {
    return savedTheme;
  }
  
  // Check system preference
  if (typeof window !== 'undefined' && window.matchMedia) {
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return systemDark ? 'dark' : 'light';
  }
  
  return 'light';
};

// Theme provider component
interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);
  const [customColors, setCustomColorsState] = useState<CustomThemeColors | null>(null);

  // Load saved theme and custom colors from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('agent-world-theme') as Theme | null;
    const savedCustomColors = localStorage.getItem('agent-world-custom-colors');
    
    if (savedTheme && ['light', 'dark', 'custom'].includes(savedTheme)) {
      setThemeState(savedTheme);
    }
    
    if (savedCustomColors) {
      try {
        const parsedColors = JSON.parse(savedCustomColors) as CustomThemeColors;
        setCustomColorsState(parsedColors);
      } catch (e) {
        console.error('Failed to parse custom colors:', e);
      }
    }
  }, []);

  // Save theme and custom colors to localStorage when they change
  useEffect(() => {
    localStorage.setItem('agent-world-theme', theme);
    
    if (theme === 'custom' && customColors) {
      localStorage.setItem('agent-world-custom-colors', JSON.stringify(customColors));
    } else if (theme !== 'custom') {
      localStorage.removeItem('agent-world-custom-colors');
    }
    
    // Update HTML class for dark mode
    const html = document.documentElement;
    if (theme === 'dark') {
      html.classList.add('dark');
      html.classList.remove('light');
    } else {
      html.classList.remove('dark');
      html.classList.add('light');
    }
  }, [theme, customColors]);

  // Set theme handler
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    
    // If switching from custom to another theme, reset custom colors
    if (newTheme !== 'custom') {
      setCustomColorsState(null);
    }
  };

  // Set custom colors handler
  const setCustomColors = (colors: CustomThemeColors) => {
    setCustomColorsState(colors);
    // If custom colors are set and theme is not custom, switch to custom
    if (theme !== 'custom') {
      setThemeState('custom');
    }
  };

  const contextValue: ThemeContextType = {
    theme,
    setTheme,
    customColors,
    setCustomColors,
    themes: availableThemes,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Custom hook to use theme context
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Export context for direct access if needed
export { ThemeContext };
export default ThemeProvider;
