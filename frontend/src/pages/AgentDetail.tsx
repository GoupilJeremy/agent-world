/**
 * Agent World - Agent Detail Page
 * Page de détails d'un agent
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, Link } from 'react-router-dom';
import Button from '../components/DesignSystem/Button';
import { ArrowLeft, Play, Edit, Trash2 } from 'lucide-react';

const AgentDetailPage: React.FC = () => {
  const { t } = useTranslation(['common', 'agents']);
  const { id } = useParams<{ id: string }>();

  return (
    <div className="min-h-screen bg-surface text-text-primary p-6 md:p-12">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="flex items-center gap-4 mb-8 animate-fade-in">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/agents">
              <ArrowLeft className="w-4 h-4" />
              <span className="ml-2">{t('back')}</span>
            </Link>
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{t('agents:agentDetails')}</h1>
            <p className="text-text-secondary mt-1">
              Agent ID: {id}
            </p>
          </div>
        </header>

        {/* Agent Card */}
        <div className="bg-surface-elevated border border-border-primary rounded-xl p-8 mb-8 animate-slide-in-top">
          <div className="flex items-start gap-6">
            <div className="w-16 h-16 bg-primary-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <span className="text-primary-600 text-3xl">🤖</span>
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">Agent Name</h2>
              <p className="text-text-secondary mb-4">
                Description of this AI agent
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-primary-50 text-primary-600 rounded-full text-sm font-medium">
                  Active
                </span>
                <span className="px-3 py-1 bg-surface-sunken text-text-secondary rounded-full text-sm font-medium">
                  Chat
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 animate-slide-in-top animation-delay-100">
          <Button variant="primary" leftIcon={<Play className="w-4 h-4" />}>
            {t('agents:runAgent')}
          </Button>
          <Button variant="outline" leftIcon={<Edit className="w-4 h-4" />}>
            {t('edit')}
          </Button>
          <Button variant="danger" leftIcon={<Trash2 className="w-4 h-4" />}>
            {t('delete')}
          </Button>
        </div>

        {/* Tabs */}
        <div className="mt-12 border-t border-border-primary">
          <nav className="flex gap-8 mb-8" aria-label="Tabs">
            {['Configuration', 'Executions', 'Logs', 'Settings'].map((tab) => (
              <button
                key={tab}
                className="py-2 px-1 border-b-2 border-transparent text-text-secondary hover:text-text-primary hover:border-border-secondary transition-colors"
              >
                {tab}
              </button>
            ))}
          </nav>
          <div className="py-4">
            <p className="text-text-secondary">
              Content for the selected tab will appear here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentDetailPage;
