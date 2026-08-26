/**
 * Agent World - SkipLink Component
 * Lien de navigation pour sauter le contenu (accessibilité)
 * Conforme aux exigences US-061 : Accessibilité (WCAG 2.1 AA)
 */

import React from 'react';
import { useTranslation } from 'react-i18next';

const SkipLink: React.FC = () => {
  const { t } = useTranslation('accessibility');

  return (
    <a
      href="#main-content"
      className="skip-link"
      aria-label={t('skipToMainContent')}
    >
      {t('skipToMainContent')}
    </a>
  );
};

export default SkipLink;
