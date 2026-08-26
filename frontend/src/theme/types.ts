/**
 * Agent World - Theme Types
 * Types TypeScript pour le système de thèmes
 */

export type Theme = 'light' | 'dark' | 'custom';

export interface ThemeColors {
  // Primary colors (Indigo)
  primary50: string;
  primary100: string;
  primary200: string;
  primary300: string;
  primary400: string;
  primary500: string;
  primary600: string;
  primary700: string;
  primary800: string;
  primary900: string;
  
  // Secondary colors (Violet)
  secondary50: string;
  secondary100: string;
  secondary200: string;
  secondary300: string;
  secondary400: string;
  secondary500: string;
  secondary600: string;
  
  // Success colors (Emerald)
  success50: string;
  success100: string;
  success200: string;
  success500: string;
  success600: string;
  success700: string;
  
  // Error colors (Red)
  error50: string;
  error100: string;
  error500: string;
  error600: string;
  error700: string;
  
  // Warning colors (Amber)
  warning50: string;
  warning100: string;
  warning500: string;
  warning600: string;
  
  // Info colors (Blue)
  info50: string;
  info100: string;
  info500: string;
  info600: string;
}

export interface ThemePalette {
  // Surface colors
  surface: string;
  surfaceElevated: string;
  surfaceSunken: string;
  surfaceOverlay: string;
  
  // Text colors
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textInverse: string;
  textLink: string;
  textLinkHover: string;
  
  // Border colors
  borderPrimary: string;
  borderSecondary: string;
  borderTertiary: string;
  
  // Shadows
  shadowSm: string;
  shadowMd: string;
  shadowLg: string;
  shadowXl: string;
}

export interface CustomThemeColors extends ThemeColors {
  // Custom accent color
  accent500: string;
  accent600: string;
}

export interface ThemeConfig {
  id: string;
  name: string;
  type: Theme;
  colors: ThemeColors;
  palette: ThemePalette;
}

export interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  customColors: CustomThemeColors | null;
  setCustomColors: (colors: CustomThemeColors) => void;
  themes: ThemeConfig[];
}

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg';

export type InputVariant = 'default' | 'error' | 'success';
export type InputSize = 'sm' | 'md' | 'lg';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export type BadgeVariant = 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';

export type CardVariant = 'default' | 'elevated' | 'sunken' | 'bordered';
