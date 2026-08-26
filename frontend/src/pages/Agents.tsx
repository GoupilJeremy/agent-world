/**
 * Agent World - Agents Page
 * Page de liste des agents
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Button from '../components/DesignSystem/Button';
import Input from '../components/DesignSystem/Input';
import { Search } from 'lucide-react';

const AgentsPage: React.FC = () => {
  const { t } = useTranslation(['common', 'agents']);

  return (
    <div className="min-h-screen bg-surface text-text-primary p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4 animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold">{t('agents:agents')}</h1>
            <p className="text-text-secondary mt-2">
              {t('agents:noAgentsDescription')}
            </p>
          </div>
          <Button variant="primary" asChild>
            <Link to="/agents/new">{t('agents:createAgent')}</Link>
          </Button>
        </header>

        {/* Search Bar */}
        <div className="mb-8 animate-slide-in-top">
          <Input
            placeholder={t('agents:searchAgents')}
            leftIcon={<Search className="w-5 h-5 text-text-tertiary" />}
            fullWidth
          />
        </div>

        {/* Empty State */}
        <div className="text-center py-16">
          <div className="w-20 h-20 bg-surface-sunken rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">🤖</span>
          </div>
          <h2 className="text-xl font-semibold mb-2">{t('agents:noAgents')}</h2>
          <p className="text-text-secondary mb-6">
            {t('agents:noAgentsDescription')}
          </p>
          <Button variant="primary" asChild>
            <Link to="/agents/new">{t('agents:createAgent')}</Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AgentsPage;
