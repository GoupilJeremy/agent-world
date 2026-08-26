# 🎨 **Agent World - Design System**
*Version : 1.0.0*
*Dernière mise à jour : 26 août 2026*

---

## 📋 **Table des Matières**

1. [🎯 Introduction](#-introduction)
2. [🎨 Principes de Design](#-principes-de-design)
3. [🎨 Système de Couleurs](#-système-de-couleurs)
4. [📝 Typologie](#-typologie)
5. [📏 Espacement](#-espacement)
6. [🔲 Bordures](#-bordures)
7. [🌓 Ombres](#-ombres)
8. [🎭 Thèmes](#-thèmes)
9. [🧩 Composants](#-composants)
10. [🎬 Animations](#-animations)
11. [♿ Accessibilité](#-accessibilité)
12. [📱 Responsive Design](#-responsive-design)
13. [🔧 Utilisation](#-utilisation)
14. [📊 Bonnes Pratiques](#-bonnes-pratiques)

---

## 🎯 **Introduction**

Le **Design System d'Agent World** est un ensemble cohérent de composants, de styles et de guidelines qui assurent une expérience utilisateur unifiée sur toute la plateforme. Il a été conçu pour être :

- **Modulaire** : Chaque composant peut être utilisé indépendamment
- **Consistant** : Mêmes couleurs, typographie et comportements partout
- **Accessible** : Conforme aux standards WCAG 2.1 AA
- **Personnalisable** : Thèmes light/dark/custom supportés
- **Performant** : Optimisé pour les animations 60 FPS

Ce document fait partie de l'**US-060 : Design System** de l'EPIC 9 (Expérience Utilisateur).

---

## 🎨 **Principes de Design**

### **Philosophie**
- **Simplicité** : Moins de complexity = meilleure UX
- **Clarté** : Chaque élément doit avoir un but clair
- **Cohérence** : Expérience unifiée sur toute la plateforme
- **Accessibilité** : Conçu pour tous les utilisateurs
- **Performance** : Animations fluides, pas de jank

### **Inspirations**
- Material Design (Google)
- Ant Design (Ant Group)
- Tailwind UI
- Radix UI

---

## 🎨 **Système de Couleurs**

### **Palette Principale**

| Couleur | Code Hex | Utilisation | Accessibilité (Contraste) |
|---------|----------|-------------|---------------------------|
| Primary 500 | `#6366F1` | Boutons principaux, liens | 4.5:1 sur blanc |
| Primary 600 | `#4F46E5` | Hover states | 7:1 sur blanc |
| Primary 700 | `#4338CA` | Active states | - |
| Secondary 500 | `#8B5CF6` | Boutons secondaires | 4.5:1 sur blanc |
| Success 500 | `#10B981` | Messages de succès | 4.5:1 sur blanc |
| Error 500 | `#EF4444` | Messages d'erreur | 4.5:1 sur blanc |
| Warning 500 | `#F59E0B` | Messages d'avertissement | 4.5:1 sur blanc |
| Info 500 | `#3B82F6` | Messages d'information | 4.5:1 sur blanc |

### **Palette de Surface**

#### **Thème Clair (Light)**
| Éléments | Couleur | Code Hex |
|----------|---------|----------|
| Surface | Blanc | `#FFFFFF` |
| Surface Élevée | Blanc | `#FFFFFF` |
| Surface Enfoncée | Gris très clair | `#F9FAFB` |
| Texte Primaire | Gris foncé | `#1F2937` |
| Texte Secondaire | Gris moyen | `#6B7280` |
| Texte Tertiaire | Gris clair | `#9CA3AF` |
| Bordure Primaire | Gris très clair | `#E5E7EB` |
| Bordure Secondaire | Gris clair | `#D1D5DB` |

#### **Thème Sombre (Dark)**
| Éléments | Couleur | Code Hex |
|----------|---------|----------|
| Surface | Gris foncé | `#1F2937` |
| Surface Élevée | Gris moyen | `#374151` |
| Surface Enfoncée | Noir | `#111827` |
| Texte Primaire | Blanc | `#F9FAFB` |
| Texte Secondaire | Gris clair | `#D1D5DB` |
| Texte Tertiaire | Gris moyen | `#9CA3AF` |
| Bordure Primaire | Gris moyen | `#374151` |
| Bordure Secondaire | Gris clair | `#4B5563` |

### **Variables CSS**

Toutes les couleurs sont disponibles via des **CSS Custom Properties** :

```css
/* Couleurs primaires */
--color-primary-50: #EEF2FF;
--color-primary-500: #6366F1;
--color-primary-600: #4F46E5;

/* Couleurs de surface */
--color-surface: #FFFFFF; /* Light */ / #1F2937; /* Dark */
--color-surface-elevated: #FFFFFF;
--color-surface-sunken: #F9FAFB;

/* Couleurs de texte */
--color-text-primary: #1F2937; /* Light */ / #F9FAFB; /* Dark */
--color-text-secondary: #6B7280;

/* Couleurs de bordure */
--color-border-primary: #E5E7EB; /* Light */ / #374151; /* Dark */
```

### **Utilisation dans Tailwind**

Le Design System étend la configuration Tailwind avec des couleurs personnalisées :

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EEF2FF',
          500: '#6366F1',
          // ...
        },
        // ...
      }
    }
  }
}
```

Utilisation dans les composants :
```tsx
<button className="bg-primary-500 text-white hover:bg-primary-600">
  Primary Button
</button>
```

---

## 📝 **Typologie**

### **Polices**

| Type | Police | Source | Utilisation |
|------|--------|--------|-------------|
| Sans Serif | Inter | Google Fonts | Texte principal |
| Mono | Fira Code | Google Fonts | Code, terminals |

### **Hiérarchie**

| Niveau | Taille | Poids | Code CSS |
|--------|--------|-------|----------|
| h1 | 2.25rem (36px) | 700 (Bold) | `text-4xl font-bold` |
| h2 | 1.875rem (30px) | 700 (Bold) | `text-3xl font-bold` |
| h3 | 1.5rem (24px) | 700 (Bold) | `text-2xl font-bold` |
| h4 | 1.25rem (20px) | 600 (Semibold) | `text-xl font-semibold` |
| h5 | 1.125rem (18px) | 600 (Semibold) | `text-lg font-semibold` |
| h6 | 1rem (16px) | 600 (Semibold) | `text-base font-semibold` |
| Body | 1rem (16px) | 400 (Normal) | `text-base` |
| Small | 0.875rem (14px) | 400 (Normal) | `text-sm` |
| Code | 0.875rem (14px) | 400 (Normal) | `text-sm font-mono` |

### **Variables CSS**

```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'Fira Code', Monaco, Consolas, monospace;
```

---

## 📏 **Espacement**

### **Système**

L'espacement suit un système basé sur les multiples de `0.25rem` (4px) :

| Nom | Valeur | Rem | Utilisation |
|-----|--------|-----|-------------|
| xs | 0.25rem | 4px | Petits écarts |
| sm | 0.5rem | 8px | Espacements compacts |
| md | 1rem | 16px | Espacement standard |
| lg | 1.5rem | 24px | Espacements larges |
| xl | 2rem | 32px | Sections |
| 2xl | 3rem | 48px | Grandes sections |

### **Variables CSS**

```css
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
--spacing-2xl: 3rem;
```

### **Utilisation dans Tailwind**

```tsx
<div className="p-6 m-4 gap-8">...</div>
```

---

## 🔲 **Bordures**

### **Rayons**

| Nom | Valeur | Utilisation |
|-----|--------|-------------|
| xs | 0.125rem (2px) | Éléménents très compacts |
| sm | 0.25rem (4px) | Boutons, inputs |
| md | 0.375rem (6px) | Cartes |
| lg | 0.5rem (8px) | Cartes larges |
| xl | 0.75rem (12px) | Modales |
| 2xl | 1rem (16px) | Images, avatars |
| full | 9999px | Pills, badges |

### **Variables CSS**

```css
--radius-xs: 0.125rem;
--radius-sm: 0.25rem;
--radius-md: 0.375rem;
--radius-lg: 0.5rem;
--radius-xl: 0.75rem;
--radius-2xl: 1rem;
--radius-full: 9999px;
```

### **Utilisation dans Tailwind**

```tsx
<button className="rounded-lg">...</button>
<div className="rounded-full">...</div>
```

---

## 🌓 **Ombres**

### **Niveaux**

| Niveau | Valeur | Utilisation |
|--------|--------|-------------|
| sm | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | Élévation subtile |
| md | `0 4px 6px -1px rgb(0 0 0 / 0.1)` | Cartes |
| lg | `0 10px 15px -3px rgb(0 0 0 / 0.1)` | Modales |
| xl | `0 20px 25px -5px rgb(0 0 0 / 0.1)` | Drawer, popovers |

### **Variables CSS**

```css
/* Light Theme */
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);

/* Dark Theme */
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.3);
```

---

## 🎭 **Thèmes**

Le Design System supporte trois thèmes principaux :

### **1. Thème Clair (Light)**
- **Par défaut** : Activé par défaut
- **Couleurs** : Fond blanc, texte foncé
- **Utilisation** : Environnements bien éclairés

### **2. Thème Sombre (Dark)**
- **Activation** : `prefers-color-scheme: dark` ou sélection manuelle
- **Couleurs** : Fond sombre, texte clair
- **Utilisation** : Environnements sombres, réduction de la fatigue oculaire

### **3. Thème Personnalisé (Custom)**
- **Fonctionnalité** : Permet de personnaliser les couleurs primaires
- **Persistance** : Sauvegardé dans localStorage
- **Statut** : À implémenter (US-063)

### **Basculer entre les thèmes**

```tsx
import { useTheme } from '@/theme';

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Toggle Theme
    </button>
  );
}
```

### **Détection Automatique**

Le thème est automatiquement détecté via :
1. Préférence sauvegardée dans localStorage
2. Préférence système (`prefers-color-scheme`)
3. Thème light par défaut

---

## 🧩 **Composants**

### **Liste des Composants**

| Composant | Description | Variantes | Tailles | Statut |
|-----------|-------------|-----------|---------|--------|
| **Button** | Bouton interactif | primary, secondary, ghost, outline, danger, success | sm, md, lg | ✅ Implémenté |
| **Input** | Champ de texte | default, error, success | sm, md, lg | ✅ Implémenté |
| **Card** | Carte de contenu | default, elevated, sunken, bordered | - | ✅ Implémenté |
| **Alert** | Message d'alerte | info, success, warning, error | - | ✅ Implémenté |
| **Badge** | Badge/étiquette | default, primary, secondary, success, warning, error, info | sm, md, lg | ✅ Implémenté |
| Typography | Éléments de texte | h1-h6, p, span, code | - | ⏳ À implémenter |
| Modal | Fenêtre modale | - | sm, md, lg, full | ⏳ À implémenter |
| Dropdown | Menu déroulant | - | - | ⏳ À implémenter |
| Table | Tableau de données | - | - | ⏳ À implémenter |
| Form | Formulaire | - | - | ⏳ À implémenter |
| Tooltip | Info-bulle | - | - | ⏳ À implémenter |
| Switch | Interrupteur | - | - | ⏳ À implémenter |
| Checkbox | Case à cocher | - | - | ⏳ À implémenter |
| Radio | Bouton radio | - | - | ⏳ À implémenter |
| Select | Sélecteur | - | - | ⏳ À implémenter |

### **Button**

**Props :**
```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  isLoading?: boolean;
  fullWidth?: boolean;
}
```

**Utilisation :**
```tsx
import Button from '@/components/DesignSystem/Button';

<Button variant="primary" size="md">
  Click Me
</Button>

<Button variant="primary" leftIcon={<Plus />}>Create</Button>
<Button variant="danger" isLoading>Deleting...</Button>
```

### **Input**

**Props :**
```tsx
interface InputProps {
  variant?: 'default' | 'error' | 'success';
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  errorMessage?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}
```

**Utilisation :**
```tsx
import Input from '@/components/DesignSystem/Input';

<Input label="Email" placeholder="Enter your email" />
<Input variant="error" errorMessage="Invalid email" />
<Input leftIcon={<Search />} />
```

### **Card**

**Props :**
```tsx
interface CardProps {
  variant?: 'default' | 'elevated' | 'sunken' | 'bordered';
  header?: ReactNode;
  footer?: ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  clickable?: boolean;
}
```

**Utilisation :**
```tsx
import Card from '@/components/DesignSystem/Card';

<Card variant="elevated" hoverable>
  <Card.Header>Title</Card.Header>
  Content here
  <Card.Footer>Footer</Card.Footer>
</Card>
```

### **Alert**

**Props :**
```tsx
interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  onClose?: () => void;
  closable?: boolean;
  icon?: ReactNode;
}
```

**Utilisation :**
```tsx
import Alert from '@/components/DesignSystem/Alert';

<Alert variant="success" title="Success!" closable>
  Your changes have been saved.
</Alert>

<Alert variant="error" onClose={() => console.log('closed')}>
  An error occurred.
</Alert>
```

### **Badge**

**Props :**
```tsx
interface BadgeProps {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}
```

**Utilisation :**
```tsx
import Badge from '@/components/DesignSystem/Badge';

<Badge variant="success">Active</Badge>
<Badge variant="primary" dot>Online</Badge>
<Badge variant="warning" size="lg">Warning</Badge>
```

---

## 🎬 **Animations**

### **Keyframes Disponibles**

| Nom | Description | Durée par défaut |
|-----|-------------|------------------|
| fadeIn | Apparition progressive | 0.2s |
| fadeOut | Disparition progressive | 0.2s |
| slideInFromTop | Glissement depuis le haut | 0.3s |
| slideInFromBottom | Glissement depuis le bas | 0.3s |
| slideInFromLeft | Glissement depuis la gauche | 0.3s |
| slideInFromRight | Glissement depuis la droite | 0.3s |
| scaleIn | Zoom d'apparition | 0.2s |
| scaleOut | Zoom de disparition | 0.2s |
| pulse | Effet de pulsation | 0.5s |
| shake | Effet de secousse | 0.5s |
| spin | Rotation continue | 1s (infinite) |
| bounce | Rebond | 1s (infinite) |
| float | Flottaison | 3s (infinite) |
| glow | Effet de lueur | 2s (infinite) |

### **Classes d'Animation**

```css
/* Animations d'entrée */
.animate-fade-in { animation: fadeIn 0.2s ease-out forwards; }
.animate-slide-in-top { animation: slideInFromTop 0.3s ease-out forwards; }
.animate-scale-in { animation: scaleIn 0.2s ease-out forwards; }

/* Animations de feedback */
.animate-pulse { animation: pulse 0.5s ease-in-out; }
.animate-shake { animation: shake 0.5s ease-in-out; }

/* Animations continues */
.animate-spin { animation: spin 1s linear infinite; }
.animate-bounce { animation: bounce 1s ease-in-out infinite; }
```

### **Utilisation**

```tsx
<div className="animate-fade-in">Content</div>
<button className="hover-lift">Hover me</button>
<div className="animate-pulse">Loading...</div>
```

### **Animations de Transitions**

```css
/* Durées */
.transition-fast { transition-duration: 0.1s; }
.transition-normal { transition-duration: 0.2s; }
.transition-slow { transition-duration: 0.3s; }

/* Propriétés */
.transition-colors { transition-property: color, background-color, border-color; }
.transition-opacity { transition-property: opacity; }
.transition-transform { transition-property: transform; }

/* États */
.hover-lift:hover { transform: translateY(-2px); }
.hover-scale:hover { transform: scale(1.02); }
.active-scale:active { transform: scale(0.98); }
```

### **Optimisation des Performances**

Toutes les animations sont optimisées :
- Utilisation de `transform` et `opacity` (propriétés GPU-accélérées)
- `will-change: transform, opacity` pour les éléments animés
- `transform: translateZ(0)` pour forcer l'accélération GPU
- Support du mode réduit (`prefers-reduced-motion: reduce`)

---

## ♿ **Accessibilité**

### **Conformité WCAG 2.1 AA**

Le Design System est conçu pour être conforme aux standards WCAG 2.1 niveau AA :

#### **Couleurs et Contraste**
- ✅ Tous les textes ont un ratio de contraste ≥ 4.5:1
- ✅ Tous les textes larges (≥ 18.66px) ont un ratio ≥ 3:1
- ✅ Les couleurs ne sont pas utilisées comme seule source d'information
- ✅ Les états de focus sont clairement visibles

#### **Navigation au Clavier**
- ✅ Tous les éléments interactifs sont accessibles via Tab
- ✅ Ordre de tabulation logique
- ✅ États de focus visibles (outline ou border)
- ✅ Skip links disponibles pour sauter la navigation

#### **Éléments de Formulaire**
- ✅ Chaque `<input>` a un `<label>` associé
- ✅ Messages d'erreur accessibles
- ✅ Attributs ARIA appropriés (`aria-label`, `aria-invalid`, etc.)
- ✅ Validation accessible

#### **Semantique HTML**
- ✅ Utilisation des balises HTML appropriées
- ✅ Hiérarchie des titres correcte (h1 > h2 > h3 > ...)
- ✅ Langue du document spécifiée

#### **Contenu Dynamique**
- ✅ Les changements de contenu sont annoncés aux screen readers
- ✅ Les modales ont un focus trap
- ✅ Les notifications sont accessibles

### **Outils de Test**

- **Lighthouse** (intégré à Chrome DevTools)
- **axe-core** (extension Chrome)
- **WAVE** (webaim.org)
- **NVDA** (screen reader pour Windows)
- **VoiceOver** (screen reader pour macOS)

### **Score Cible**
- **Lighthouse Accessibility** : > 90/100
- **axe-core** : 0 violations

---

## 📱 **Responsive Design**

### **Breakpoints**

Le Design System utilise les breakpoints Tailwind par défaut :

| Breakpoint | Min-Width | Utilisation |
|------------|-----------|-------------|
| sm | 640px | Téléphones |
| md | 768px | Tablettes |
| lg | 1024px | Petits écrans |
| xl | 1280px | Grands écrans |
| 2xl | 1536px | Très grands écrans |

### **Approche Mobile-First**

```css
/* Par défaut : mobile */
.button { padding: 0.5rem 1rem; }

/* Tablette et + */
@media (min-width: 768px) {
  .button { padding: 0.75rem 1.5rem; }
}
```

### **Utilisation dans Tailwind**

```tsx
<div className="p-4 md:p-6 lg:p-8">...</div>
<div className="text-sm md:text-base">...</div>
<div className="block md:hidden">...</div>
```

---

## 🔧 **Utilisation**

### **Installation**

Tous les composants du Design System sont exportés depuis :

```tsx
import { Button, Input, Card, Alert, Badge } from '@/components/DesignSystem';
```

### **Configuration du Thème**

1. **Wrapper l'application avec ThemeProvider** :

```tsx
// main.tsx
import { ThemeProvider } from '@/theme';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ThemeProvider>
    <App />
  </ThemeProvider>
);
```

2. **Utiliser le thème dans les composants** :

```tsx
import { useTheme } from '@/theme';

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Toggle Theme
    </button>
  );
}
```

### **Configuration i18n**

1. **Wrapper l'application avec i18n** :

```tsx
// main.tsx
import './i18n';

// L'initialisation i18n se fait automatiquement
```

2. **Utiliser les traductions** :

```tsx
import { useTranslation } from 'react-i18next';

function Welcome() {
  const { t } = useTranslation('common');
  
  return <h1>{t('welcome')}</h1>;
}
```

---

## 📊 **Bonnes Pratiques**

### **Do's**

✅ **Toujours utiliser les composants du Design System**
- Préférez `<Button>` à `<button>`
- Préférez `<Input>` à `<input>`

✅ **Respecter les conventions de nommage**
- Utilisez les classes Tailwind existantes
- Évitez les styles inline

✅ **Documenter votre code**
- Ajoutez des commentaires JSDoc
- Expliquez les props complexes

✅ **Tester l'accessibilité**
- Vérifiez avec Lighthouse
- Testez la navigation au clavier
- Utilisez un screen reader

✅ **Optimiser les performances**
- Évitez les animations coûteuses
- Utilisez `will-change` pour les éléments animés
- Minimisez les re-renders

### **Don'ts**

❌ **Ne pas utiliser de styles inline**
- ❌ `<div style={{ color: 'red' }}>`
- ✅ `<div className="text-error-500">`

❌ **Ne pas créer de nouveaux composants sans nécessité**
- Vérifiez d'abord si un composant similaire existe

❌ **Ne pas ignorer l'accessibilité**
- Tous les éléments interactifs doivent être accessibles

❌ **Ne pas utiliser de couleurs fixes**
- ❌ `<div style={{ color: '#6366F1' }}>`
- ✅ `<div className="text-primary-500">`

❌ **Ne pas surcharger les animations**
- Trop d'animations peuvent distraire et nuire aux performances

---

## 📚 **Ressources**

### **Documentation**
- [Tailwind CSS](https://tailwindcss.com/docs)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Design System Checklist](https://www.designsystemchecklist.com/)

### **Outils**
- [Tailwind Play](https://play.tailwindcss.com/)
- [Color Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse/)
- [axe-core](https://github.com/dequelabs/axe-core)

### **Inspirations**
- [Material Design](https://m3.material.io/)
- [Ant Design](https://ant.design/)
- [Radix UI](https://www.radix-ui.com/)
- [Chakra UI](https://chakra-ui.com/)

---

## 📝 **Changelog**

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 26 août 2026 | Création initiale du Design System (US-060) |
| 1.0.0 | 26 août 2026 | Ajout du système de thèmes (US-063) |
| 1.0.0 | 26 août 2026 | Ajout des animations (US-064) |

---

*Document généré par Mistral Vibe - Co-Authored-By: Mistral Vibe <vibe@mistral.ai>*
