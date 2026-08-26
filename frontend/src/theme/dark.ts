/**
 * Agent World - Dark Theme Configuration
 * Configuration du thème sombre
 */

import { ThemeConfig } from './types';

export const darkTheme: ThemeConfig = {
  id: 'dark',
  name: 'Sombre',
  type: 'dark',
  colors: {
    // Primary colors (Indigo) - Lighter shades for dark mode
    primary50: '#1E1B4B',
    primary100: '#312E81',
    primary200: '#3730A3',
    primary300: '#4338CA',
    primary400: '#4F46E5',
    primary500: '#6366F1',
    primary600: '#818CF8',
    primary700: '#A5B4FC',
    primary800: '#C7D2FE',
    primary900: '#E0E7FF',
    
    // Secondary colors (Violet) - Lighter shades for dark mode
    secondary50: '#2E1065',
    secondary100: '#4C1D95',
    secondary200: '#5B21B6',
    secondary300: '#6D28D9',
    secondary400: '#7C3AED',
    secondary500: '#8B5CF6',
    secondary600: '#A78BFA',
    
    // Success colors (Emerald) - Lighter shades for dark mode
    success50: '#022C22',
    success100: '#064E3B',
    success200: '#065F46',
    success500: '#10B981',
    success600: '#34D399',
    success700: '#6EE7B7',
    
    // Error colors (Red) - Lighter shades for dark mode
    error50: '#450A0A',
    error100: '#7F1D1D',
    error500: '#EF4444',
    error600: '#F87171',
    error700: '#FCA5A5',
    
    // Warning colors (Amber) - Lighter shades for dark mode
    warning50: '#451A03',
    warning100: '#78350F',
    warning500: '#F59E0B',
    warning600: '#FBBF24',
    
    // Info colors (Blue) - Lighter shades for dark mode
    info50: '#172554',
    info100: '#1E3A8A',
    info500: '#3B82F6',
    info600: '#60A5FA',
  },
  palette: {
    // Surface colors
    surface: '#1F2937',
    surfaceElevated: '#374151',
    surfaceSunken: '#111827',
    surfaceOverlay: 'rgba(0, 0, 0, 0.7)',
    
    // Text colors
    textPrimary: '#F9FAFB',
    textSecondary: '#D1D5DB',
    textTertiary: '#9CA3AF',
    textInverse: '#1F2937',
    textLink: '#818CF8',
    textLinkHover: '#C7D2FE',
    
    // Border colors
    borderPrimary: '#374151',
    borderSecondary: '#4B5563',
    borderTertiary: '#6B7280',
    
    // Shadows - More visible in dark mode
    shadowSm: '0 1px 2px 0 rgb(0 0 0 / 0.3)',
    shadowMd: '0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.3)',
    shadowLg: '0 10px 15px -3px rgb(0 0 0 / 0.4), 0 4px 6px -4px rgb(0 0 0 / 0.3)',
    shadowXl: '0 20px 25px -5px rgb(0 0 0 / 0.5), 0 8px 10px -6px rgb(0 0 0 / 0.4)',
  },
};

export default darkTheme;
