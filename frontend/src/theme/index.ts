/**
 * Agent World - Theme Module
 * Module principal pour l'export des fonctionnalités de thème
 */

export { default as ThemeProvider } from './ThemeProvider';
export { useTheme } from './ThemeProvider';
export type { Theme, ThemeConfig, ThemeContextType, CustomThemeColors } from './types';
export { lightTheme } from './light';
export { darkTheme } from './dark';
export type {
  ButtonVariant,
  ButtonSize,
  InputVariant,
  InputSize,
  AlertVariant,
  BadgeVariant,
  CardVariant,
} from './types';
