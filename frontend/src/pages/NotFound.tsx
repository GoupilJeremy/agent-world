/**
 * Agent World - Not Found Page
 * Page 404
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Button from '../components/DesignSystem/Button';

const NotFoundPage: React.FC = () => {
  const { t } = useTranslation('common');

  return (
    <div className="min-h-screen bg-surface text-text-primary flex items-center justify-center p-6">
      <div className="text-center animate-fade-in">
        <div className="w-24 h-24 bg-surface-sunken rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-6xl font-bold text-text-tertiary">404</span>
        </div>
        <h1 className="text-3xl font-bold mb-4">{t('pageNotFound')}</h1>
        <p className="text-text-secondary mb-8 max-w-md mx-auto">
          {t('pageNotFoundDescription')}
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button variant="primary" asChild>
            <Link to="/">{t('goToHome')}</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/agents">{t('agents')}</Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
