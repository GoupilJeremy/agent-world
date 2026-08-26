/**
 * Agent World - Light Theme Configuration
 * Configuration du thème clair
 */

import { ThemeConfig } from './types';

export const lightTheme: ThemeConfig = {
  id: 'light',
  name: 'Clair',
  type: 'light',
  colors: {
    // Primary colors (Indigo)
    primary50: '#EEF2FF',
    primary100: '#E0E7FF',
    primary200: '#C7D2FE',
    primary300: '#A5B4FC',
    primary400: '#818CF8',
    primary500: '#6366F1',
    primary600: '#4F46E5',
    primary700: '#4338CA',
    primary800: '#3730A3',
    primary900: '#312E81',
    
    // Secondary colors (Violet)
    secondary50: '#F5F3FF',
    secondary100: '#EDE9FE',
    secondary200: '#DDD6FE',
    secondary300: '#C4B5FD',
    secondary400: '#A78BFA',
    secondary500: '#8B5CF6',
    secondary600: '#7C3AED',
    
    // Success colors (Emerald)
    success50: '#ECFDF5',
    success100: '#D1FAE5',
    success200: '#A7F3D0',
    success500: '#10B981',
    success600: '#059669',
    success700: '#047857',
    
    // Error colors (Red)
    error50: '#FEF2F2',
    error100: '#FEE2E2',
    error500: '#EF4444',
    error600: '#DC2626',
    error700: '#B91C1C',
    
    // Warning colors (Amber)
    warning50: '#FFFBEB',
    warning100: '#FEF3C7',
    warning500: '#F59E0B',
    warning600: '#D97706',
    
    // Info colors (Blue)
    info50: '#EFF6FF',
    info100: '#DBEAFE',
    info500: '#3B82F6',
    info600: '#2563EB',
  },
  palette: {
    // Surface colors
    surface: '#FFFFFF',
    surfaceElevated: '#FFFFFF',
    surfaceSunken: '#F9FAFB',
    surfaceOverlay: 'rgba(0, 0, 0, 0.5)',
    
    // Text colors
    textPrimary: '#1F2937',
    textSecondary: '#6B7280',
    textTertiary: '#9CA3AF',
    textInverse: '#FFFFFF',
    textLink: '#6366F1',
    textLinkHover: '#4F46E5',
    
    // Border colors
    borderPrimary: '#E5E7EB',
    borderSecondary: '#D1D5DB',
    borderTertiary: '#9CA3AF',
    
    // Shadows
    shadowSm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    shadowMd: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    shadowLg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    shadowXl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  },
};

export default lightTheme;
