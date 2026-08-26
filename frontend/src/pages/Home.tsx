/**
 * Agent World - Home Page
 * Page d'accueil de l'application
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Button from '../components/DesignSystem/Button';

const HomePage: React.FC = () => {
  const { t } = useTranslation('common');

  return (
    <div className="min-h-screen bg-surface text-text-primary p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <section className="text-center py-12 md:py-20 animate-fade-in">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            {t('appName')}
          </h1>
          <p className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto mb-8">
            {t('appDescription')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary" size="lg" asChild>
              <Link to="/agents">{t('getStarted')}</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link to="/settings">{t('settings')}</Link>
            </Button>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16">
          <h2 className="text-3xl font-bold text-center mb-12">
            {t('agentCapabilities')}
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-surface-elevated p-6 rounded-xl border border-border-primary hover:shadow-md transition-all duration-300 animate-slide-in-top animation-delay-${i * 100}"
              >
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                  <span className="text-primary-600 text-2xl font-bold">{i}</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">Feature {i}</h3>
                <p className="text-text-secondary">
                  Description of feature {i} goes here.
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="text-center py-16">
          <h2 className="text-3xl font-bold mb-6">
            Ready to create your first AI agent?
          </h2>
          <Button variant="primary" size="lg" asChild>
            <Link to="/agents">{t('createAgent')}</Link>
          </Button>
        </section>
      </div>
    </div>
  );
};

export default HomePage;
