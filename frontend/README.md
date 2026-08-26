# 🚀 **Agent World - Frontend**
*Version : 0.4.3*
*Dernière mise à jour : 26 août 2026*

---

## 📋 **Table des Matières**

1. [🎯 Introduction](#-introduction)
2. [📦 Prérequis](#-prérequis)
3. [🚀 Installation](#-installation)
4. [🏗️ Architecture](#-architecture)
5. [🎨 Design System](#-design-system)
6. [🌓 Thèmes](#-thèmes)
7. [🌍 Internationalisation](#-internationalisation)
8. [🎬 Animations](#-animations)
9. [♿ Accessibilité](#-accessibilité)
10. [📁 Structure du Projet](#-structure-du-projet)
11. [⚛️ Composants Principaux](#-composants-principaux)
12. [🚀 Scripts Disponibles](#-scripts-disponibles)
13. [🔧 Configuration](#-configuration)
14. [💡 Bonnes Pratiques](#-bonnes-pratiques)
15. [📚 Ressources](#-ressources)

---

## 🎯 **Introduction**

Bienvenue dans le **frontend d'Agent World** ! Ce projet est construit avec **React 18**, **TypeScript**, **Vite** et **Tailwind CSS** pour offrir une expérience utilisateur moderne, performante et accessible.

Ce frontend fait partie de l'**EPIC 9 : Expérience Utilisateur (UX)** et implémente :
- ✅ **Design System** cohérent (US-060)
- ✅ **Thèmes personnalisables** (US-063)
- ✅ **Animations fluides** (US-064)
- ✅ **Internationalisation (i18n)** (US-062)
- ✅ **Accessibilité WCAG 2.1 AA** (US-061)

---

## 📦 **Prérequis**

| Outil | Version | Description |
|-------|---------|-------------|
| **Node.js** | ≥ 18.0.0 | Runtime JavaScript |
| **npm** | ≥ 9.0.0 | Gestionnaire de packages |
| **Git** | ≥ 2.0.0 | Contrôle de version |

---

## 🚀 **Installation**

### **1. Cloner le dépôt**

```bash
cd agent-world
```

### **2. Installer les dépendances**

```bash
cd frontend
npm install
```

Cette commande installe toutes les dépendances définies dans `package.json` :
- React 18.2.0
- TypeScript 5.3.0
- Vite 5.0.0
- Tailwind CSS 3.4.0
- i18next 23.7.0
- Lucide React (icônes)
- Et bien d'autres...

### **3. Démarrer le serveur de développement**

```bash
npm run dev
```

L'application sera disponible à l'adresse : [http://localhost:3000](http://localhost:3000)

Le serveur inclut :
- **Hot Module Replacement (HMR)** : Les modifications sont automatiquement rechargées
- **Proxy API** : Les requêtes vers `/api` sont redirigées vers `http://localhost:5000`

### **4. Construire pour la production**

```bash
npm run build
```

Les fichiers optimisés seront générés dans le dossier `dist/`.

### **5. Prévisualiser la version de production**

```bash
npm run preview
```

---

## 🏗️ **Architecture**

```
frontend/
├── public/                    # Fichiers statiques
│   └── favicon.svg            # Icône de l'application
│
├── src/
│   ├── components/            # Composants React
│   │   ├── Accessibility/    # Composants d'accessibilité
│   │   │   ├── SkipLink.tsx  # Lien pour sauter la navigation
│   │   │   └── index.ts
│   │   │
│   │   └── DesignSystem/     # Design System (US-060)
│   │       ├── Alert/        # Composant Alert
│   │       ├── Badge/        # Composant Badge
│   │       ├── Button/       # Composant Button
│   │       ├── Card/         # Composant Card
│   │       ├── Input/        # Composant Input
│   │       └── index.ts      # Export des composants
│   │
│   ├── hooks/                # Hooks React personnalisés
│   │
│   ├── i18n/                 # Internationalisation (US-062)
│   │   └── index.ts          # Configuration i18next
│   │
│   ├── locales/              # Fichiers de traduction
│   │   ├── en/               # Anglais
│   │   │   ├── common.json
│   │   │   ├── accessibility.json
│   │   │   ├── agents.json
│   │   │   ├── settings.json
│   │   │   └── validation.json
│   │   └── fr/               # Français
│   │       ├── common.json
│   │       ├── accessibility.json
│   │       ├── agents.json
│   │       ├── settings.json
│   │       └── validation.json
│   │
│   ├── pages/                # Pages de l'application
│   │   ├── Home.tsx          # Page d'accueil
│   │   ├── Agents.tsx        # Liste des agents
│   │   ├── AgentDetail.tsx   # Détails d'un agent
│   │   ├── Settings.tsx      # Paramètres
│   │   ├── NotFound.tsx      # Page 404
│   │   └── index.ts          # Export des pages
│   │
│   ├── styles/               # Styles CSS
│   │   ├── index.css         # Styles globaux + variables CSS
│   │   └── animations.css    # Animations (US-064)
│   │
│   ├── theme/                # Système de thèmes (US-063)
│   │   ├── types.ts          # Types TypeScript
│   │   ├── light.ts          # Configuration thème clair
│   │   ├── dark.ts           # Configuration thème sombre
│   │   ├── ThemeProvider.tsx # Fournisseur de contexte
│   │   └── index.ts          # Export du module
│   │
│   ├── types/                # Types TypeScript globaux
│   │   └── index.ts
│   │
│   ├── App.tsx               # Composant principal
│   ├── main.tsx              # Point d'entrée
│   └── vite-env.d.ts         # Déclarations de types Vite
│
├── .gitignore                # Fichiers à ignorer
├── index.html                # Template HTML
├── package.json              # Configuration npm
├── postcss.config.js         # Configuration PostCSS
├── tailwind.config.js        # Configuration Tailwind CSS
├── tsconfig.json             # Configuration TypeScript
├── tsconfig.node.json        # Configuration TypeScript (Node)
├── vite.config.ts            # Configuration Vite
└── README.md                 # Ce fichier
```

---

## 🎨 **Design System**

Le **Design System** d'Agent World (US-060) est un ensemble de composants, styles et guidelines qui assurent une expérience utilisateur cohérente.

### **Composants Disponibles**

| Composant | Description | Variantes | Tailles |
|-----------|-------------|-----------|---------|
| **Button** | Bouton interactif | primary, secondary, ghost, outline, danger, success | sm, md, lg |
| **Input** | Champ de texte | default, error, success | sm, md, lg |
| **Card** | Carte de contenu | default, elevated, sunken, bordered | - |
| **Alert** | Message d'alerte | info, success, warning, error | - |
| **Badge** | Badge/étiquette | default, primary, secondary, success, warning, error, info | sm, md, lg |

**Utilisation :**
```tsx
import { Button, Input, Card, Alert, Badge } from '@/components/DesignSystem';

<Button variant="primary" size="md">Click Me</Button>
<Input label="Email" variant="error" errorMessage="Invalid email" />
<Card variant="elevated" hoverable>Content</Card>
<Alert variant="success" title="Success!" closable>Saved!</Alert>
<Badge variant="primary" dot>Online</Badge>
```

### **Documentation Complète**

Voir [DESIGN_SYSTEM.md](../../docs/DESIGN_SYSTEM.md) pour :
- Système de couleurs complet
- Typologie
- Espacement
- Bordures
- Ombres
- Animations
- Guidelines d'accessibilité
- Bonnes pratiques

---

## 🌓 **Thèmes**

Le frontend supporte trois thèmes : **clair**, **sombre** et **personnalisé** (US-063).

### **Basculer entre les thèmes**

```tsx
import { useTheme } from '@/theme';

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  
  return (
    <div className="flex gap-2">
      <button onClick={() => setTheme('light')}>Light</button>
      <button onClick={() => setTheme('dark')}>Dark</button>
      <button onClick={() => setTheme('custom')}>Custom</button>
    </div>
  );
}
```

### **Caractéristiques**

- ✅ **Persistance** : Le thème est sauvegardé dans localStorage
- ✅ **Détection automatique** : Utilise `prefers-color-scheme` pour détecter la préférence système
- ✅ **Application automatique** : Les variables CSS sont mises à jour automatiquement
- ✅ **Thème personnalisé** : Permet de modifier les couleurs primaires (à implémenter)

---

## 🌍 **Internationalisation (i18n)**

L'application supporte **Français (FR)** et **Anglais (EN)** via **i18next** et **react-i18next** (US-062).

### **Utilisation**

```tsx
import { useTranslation } from 'react-i18next';

function Welcome() {
  const { t, i18n } = useTranslation('common');
  
  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };
  
  return (
    <div>
      <h1>{t('welcome')}</h1>
      <button onClick={() => changeLanguage('fr')}>Français</button>
      <button onClick={() => changeLanguage('en')}>English</button>
    </div>
  );
}
```

### **Namespaces Disponibles**

| Namespace | Description | Nombre de clés |
|-----------|-------------|----------------|
| `common` | Traductions générales | ~100 |
| `accessibility` | Traductions pour l'accessibilité | ~70 |
| `agents` | Traductions pour les agents | ~250 |
| `settings` | Traductions pour les paramètres | ~200 |
| `validation` | Messages de validation | ~150 |

**Total** : ~770 clés traduites dans chaque langue

### **Caractéristiques**

- ✅ **Détection automatique** : Détecte la langue du navigateur
- ✅ **Persistance** : Sauvegarde la préférence dans localStorage
- ✅ **Chargement dynamique** : Charge les traductions à la demande
- ✅ **Fallback** : Utilise le français comme langue par défaut

---

## 🎬 **Animations**

Le frontend inclut un système complet d'animations (US-064) :

### **Keyframes Disponibles**

- `fadeIn`, `fadeOut` - Apparition/disparition progressive
- `slideInFromTop`, `slideInFromBottom`, `slideInFromLeft`, `slideInFromRight` - Glissements
- `scaleIn`, `scaleOut` - Effets de zoom
- `pulse`, `shake` - Feedback visuel
- `spin`, `bounce`, `float`, `glow` - Animations continues

### **Classes d'Animation**

```css
.animate-fade-in { animation: fadeIn 0.2s ease-out forwards; }
.animate-slide-in-top { animation: slideInFromTop 0.3s ease-out forwards; }
.animate-pulse { animation: pulse 0.5s ease-in-out; }
.animate-spin { animation: spin 1s linear infinite; }
```

### **Classes de Transition**

```css
.transition-fast { transition-duration: 0.1s; }
.transition-normal { transition-duration: 0.2s; }
.transition-slow { transition-duration: 0.3s; }

.hover-lift:hover { transform: translateY(-2px); }
.hover-scale:hover { transform: scale(1.02); }
.active-scale:active { transform: scale(0.98); }
```

### **Optimisation**

- ✅ **GPU Accélération** : Utilisation de `transform` et `opacity`
- ✅ **will-change** : Pour les éléments animés
- ✅ **Support réduit** : Désactive les animations avec `prefers-reduced-motion: reduce`

---

## ♿ **Accessibilité**

Le frontend est conçu pour être **100% conforme aux standards WCAG 2.1 AA** (US-061).

### **Fonctionnalités Implémentées**

- ✅ **Skip Links** : Permet de sauter la navigation
- ✅ **Focus States** : Styles de focus visibles
- ✅ **ARIA Attributes** : Attributs ARIA appropriés
- ✅ **Contraste des couleurs** : Tous les contrastes ≥ 4.5:1
- ✅ **Navigation clavier** : Tous les éléments accessibles
- ✅ **Réduction des animations** : Support de `prefers-reduced-motion`

### **Documentation Complète**

Voir [ACCESSIBILITY_AUDIT.md](../../docs/ACCESSIBILITY_AUDIT.md) pour :
- Méthodologie de test
- Résultats détaillés
- Points conformes et à améliorer
- Plan d'action

---

## 📁 **Structure du Projet**

Voir [Architecture](#-architecture) ci-dessus.

---

## ⚛️ **Composants Principaux**

### **Design System**

- **Button** : Bouton réutilisable avec 6 variantes et 3 tailles
- **Input** : Champ de texte avec validation et icônes
- **Card** : Carte de contenu avec header/footer
- **Alert** : Message d'alerte avec icônes
- **Badge** : Badge/étiquette avec dot optionnel

### **Accessibilité**

- **SkipLink** : Lien pour sauter la navigation

### **Pages**

- **Home** : Page d'accueil avec héro section
- **Agents** : Liste des agents avec recherche
- **AgentDetail** : Détails d'un agent avec actions
- **Settings** : Paramètres avec onglets
- **NotFound** : Page 404

---

## 🚀 **Scripts Disponibles**

| Commande | Description |
|----------|-------------|
| `npm run dev` | Démarre le serveur de développement |
| `npm run build` | Construit l'application pour la production |
| `npm run preview` | Prévisualise la version de production |
| `npm run lint` | Exécute ESLint |
| `npm run lint:fix` | Corrigé les problèmes ESLint |
| `npm test` | Exécute les tests avec Vitest |
| `npm run test:ui` | Exécute les tests avec interface Vitest UI |
| `npm run test:coverage` | Exécute les tests avec couverture de code |
| `npm run storybook` | Démarre Storybook |
| `npm run build-storybook` | Construit Storybook |

---

## 🔧 **Configuration**

### **Proxy API**

Le serveur de développement est configuré pour proxyfier les requêtes `/api` vers le backend (port 5000) :

```typescript
// vite.config.ts
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
    },
  },
}
```

### **Variables d'Environnement**

Créer un fichier `.env` à la racine du projet `frontend/` :

```env
# Port du serveur de développement
VITE_PORT=3000

# URL du backend
VITE_API_URL=http://localhost:5000

# Mode développement/production
NODE_ENV=development
```

---

## 💡 **Bonnes Pratiques**

### **Développement**

1. **Utiliser les composants du Design System**
   - Éviter de créer des composants custom
   - Utiliser les variantes et tailles appropriées

2. **Respecter les conventions**
   - Nommage PascalCase pour les composants
   - Nommage kebab-case pour les fichiers de traduction
   - Utiliser TypeScript pour la typage

3. **Documenter le code**
   - Ajouter des commentaires JSDoc
   - Documenter les props des composants

4. **Tester l'accessibilité**
   - Vérifier avec Lighthouse
   - Tester la navigation au clavier

### **Performance**

1. **Éviter les animations coûteuses**
   - Préférer `transform` et `opacity`
   - Utiliser `will-change` pour les éléments animés

2. **Optimiser les images**
   - Utiliser des formats modernes (WebP)
   - Compresser les images

3. **Code splitting**
   - Utiliser le lazy loading pour les composants
   - Charger les dépendances à la demande

---

## 📚 **Ressources**

### **Documentation**

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [i18next Documentation](https://www.i18next.com/)

### **Design System**

- [DESIGN_SYSTEM.md](../../docs/DESIGN_SYSTEM.md) - Documentation complète du Design System
- [ACCESSIBILITY_AUDIT.md](../../docs/ACCESSIBILITY_AUDIT.md) - Rapport d'audit d'accessibilité

### **Tutoriels**

- [Tailwind CSS Tutorial](https://tailwindcss.com/docs/utility-first)
- [React Hooks Tutorial](https://react.dev/reference/react)
- [TypeScript with React](https://www.typescriptlang.org/docs/handbook/react.html)

---

## 🤝 **Contribution**

### **Règles**

1. **Respecter le Design System**
   - Utiliser les composants existants
   - Respecter les couleurs et la typographie

2. **Écrire des tests**
   - Tests unitaires pour les composants
   - Tests d'accessibilité

3. **Documenter les modifications**
   - Mettre à jour la documentation
   - Ajouter des commentaires dans le code

4. **Suivre les conventions**
   - Respecter le linting (ESLint)
   - Respecter le formatting (Prettier)

---

## 🐛 **Dépannage**

### **Problèmes courants**

#### **1. Les styles Tailwind ne fonctionnent pas**

**Solution :**
- Vérifier que le fichier est inclus dans `tailwind.config.js`
- Vérifier que les classes sont correctement appliquées
- Redémarrer le serveur de développement

#### **2. Les traductions ne s'affichent pas**

**Solution :**
- Vérifier que le namespace est correct
- Vérifier que les fichiers JSON sont valides
- Vérifier que i18next est correctement initialisé

#### **3. Le thème ne change pas**

**Solution :**
- Vérifier que le composant est wrapé dans `ThemeProvider`
- Vérifier que localStorage fonctionne
- Vérifier qu'il n'y a pas de cache

#### **4. Les animations ne fonctionnent pas**

**Solution :**
- Vérifier que les classes CSS sont correctement appliquées
- Vérifier que le navigateur supporte les animations CSS
- Vérifier qu'il n'y a pas de conflit de styles

---

## 📜 **Licence**

Ce projet est sous licence **MIT**. Voir [LICENSE](../../LICENSE) pour plus de détails.

---

## 📞 **Support**

Pour toute question ou problème, consulter :
- [Documentation principale](../../README.md)
- [Backlog du projet](../../BACKLOG.md)
- [Roadmap](../../ROADMAP.md)

---

*Document généré par Mistral Vibe - Co-Authored-By: Mistral Vibe <vibe@mistral.ai>*
