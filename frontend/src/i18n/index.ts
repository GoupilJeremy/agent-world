/**
 * Agent World - i18n Configuration
 * Configuration de l'internationalisation
 * Conforme aux exigences US-062 : Internationalisation (i18n)
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translations (loaded dynamically in production)
// For development, we can import directly
import enCommon from '../locales/en/common.json';
import frCommon from '../locales/fr/common.json';
import enAccessibility from '../locales/en/accessibility.json';
import frAccessibility from '../locales/fr/accessibility.json';
import enAgents from '../locales/en/agents.json';
import frAgents from '../locales/fr/agents.json';
import enSettings from '../locales/en/settings.json';
import frSettings from '../locales/fr/settings.json';
import enValidation from '../locales/en/validation.json';
import frValidation from '../locales/fr/validation.json';

// Fallback translations for development
const resources = {
  en: {
    common: enCommon,
    accessibility: enAccessibility,
    agents: enAgents,
    settings: enSettings,
    validation: enValidation,
  },
  fr: {
    common: frCommon,
    accessibility: frAccessibility,
    agents: frAgents,
    settings: frSettings,
    validation: frValidation,
  },
};

// Initialize i18n
i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'fr',
    debug: process.env.NODE_ENV === 'development',
    interpolation: {
      escapeValue: false,
    },
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },
    detection: {
      order: ['navigator', 'localStorage', 'htmlTag'],
      caches: ['localStorage'],
    },
    resources, // Fallback resources for development
    ns: ['common', 'accessibility', 'agents', 'settings', 'validation'],
    defaultNS: 'common',
    saveMissing: process.env.NODE_ENV === 'development',
    missingKeyHandler: (lngs, ns, key, fallback) => {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Missing translation: ${key} in ${ns} for ${lngs.join(', ')}`);
      }
      return fallback;
    },
  });

export default i18n;
