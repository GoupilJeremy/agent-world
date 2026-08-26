/**
 * Agent World - Settings Page
 * Page des paramètres
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../theme';
import Button from '../components/DesignSystem/Button';
import { Moon, Sun, Palette, Languages, Bell, Shield, User } from 'lucide-react';

const SettingsPage: React.FC = () => {
  const { t } = useTranslation(['common', 'settings']);
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('appearance');

  const tabs = [
    { id: 'appearance', label: t('settings:appearance'), icon: Palette },
    { id: 'language', label: t('language'), icon: Languages },
    { id: 'notifications', label: t('settings:notifications'), icon: Bell },
    { id: 'security', label: t('settings:security'), icon: Shield },
    { id: 'account', label: t('settings:account'), icon: User },
  ];

  return (
    <div className="min-h-screen bg-surface text-text-primary p-6 md:p-12">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold">{t('settings:settings')}</h1>
          <p className="text-text-secondary mt-2">
            {t('settings:generalSettings')}
          </p>
        </header>

        {/* Tabs and Content */}
        <div className="grid md:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <nav className="space-y-2 animate-slide-in-left">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  activeTab === id
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-text-secondary hover:bg-surface-sunken hover:text-text-primary'
                }`}
                aria-current={activeTab === id ? 'page' : undefined}
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </button>
            ))}
          </nav>

          {/* Content */}
          <div className="md:col-span-3 bg-surface-elevated border border-border-primary rounded-xl p-8 animate-slide-in-right">
            {activeTab === 'appearance' && (
              <div>
                <h2 className="text-2xl font-semibold mb-6">{t('settings:appearance')}</h2>
                <p className="text-text-secondary mb-8">
                  {t('settings:appearanceDescription')}
                </p>

                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-2">{t('theme')}</h3>
                    <p className="text-text-secondary text-sm mb-4">
                      {t('settings:themeDescription')}
                    </p>
                    <div className="flex gap-4">
                      <Button
                        variant={theme === 'light' ? 'primary' : 'outline'}
                        leftIcon={<Sun className="w-4 h-4" />}
                        onClick={() => setTheme('light')}
                      >
                        {t('light')}
                      </Button>
                      <Button
                        variant={theme === 'dark' ? 'primary' : 'outline'}
                        leftIcon={<Moon className="w-4 h-4" />}
                        onClick={() => setTheme('dark')}
                      >
                        {t('dark')}
                      </Button>
                      <Button
                        variant={theme === 'custom' ? 'primary' : 'outline'}
                        leftIcon={<Palette className="w-4 h-4" />}
                        onClick={() => setTheme('custom')}
                      >
                        {t('custom')}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium mb-2">{t('settings:animations')}</h3>
                    <p className="text-text-secondary text-sm mb-4">
                      {t('settings:animationsDescription')}
                    </p>
                    <div className="flex gap-4">
                      <Button variant="primary">{t('settings:enableAnimations')}</Button>
                      <Button variant="outline">{t('settings:disableAnimations')}</Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'language' && (
              <div>
                <h2 className="text-2xl font-semibold mb-6">{t('language')}</h2>
                <p className="text-text-secondary mb-8">
                  {t('settings:languageDescription')}
                </p>
                <div className="flex gap-4">
                  <Button variant="primary">Français</Button>
                  <Button variant="outline">English</Button>
                </div>
              </div>
            )}

            {(activeTab === 'notifications' || activeTab === 'security' || activeTab === 'account') && (
              <div>
                <h2 className="text-2xl font-semibold mb-6">
                  {tabs.find(t => t.id === activeTab)?.label}
                </h2>
                <p className="text-text-secondary">
                  Content for {activeTab} settings will be implemented soon.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8 flex justify-end animate-slide-in-top">
          <Button variant="primary" size="lg">
            {t('settings:saveSettings')}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
