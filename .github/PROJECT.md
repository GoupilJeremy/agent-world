# 🛠️ **Agent World - Configuration GitHub**
*Guide complet pour configurer le repository GitHub*

---

## 📌 **Table des Matières**
1. [🎯 Introduction](#-introduction)
2. [📦 Structure du Repository](#-structure-du-repository)
3. [🏷️ Configuration des Labels](#-configuration-des-labels)
4. [🎯 Configuration des Milestones](#-configuration-des-milestones)
5. [📋 Configuration des Projects](#-configuration-des-projects)
6. [⚙️ Configuration de la CI/CD](#-configuration-de-la-cicd)
7. [🔒 Configuration de la Sécurité](#-configuration-de-la-sécurité)
8. [📊 Configuration des Insights](#-configuration-des-insights)
9. [🤖 Configuration des Bots](#-configuration-des-bots)
10. [📜 Checklist de Configuration](#-checklist-de-configuration)


---

## 📜 **Scripts de Configuration**

Pour faciliter la configuration, des scripts Bash ont été générés dans le dossier `scripts/` :
- [`create_github_labels.sh`](scripts/create_github_labels.sh) : Crée les 28 labels.
- [`create_github_milestones.sh`](scripts/create_github_milestones.sh) : Crée les 6 milestones.
- [`create_github_project.sh`](scripts/create_github_project.sh) : Crée le projet Kanban.
- [`create_sprint0_issues.sh`](scripts/create_sprint0_issues.sh) : Crée les 5 issues du Sprint 0.

> ⚠️ **Note** : Si les appels API GitHub sont bloqués dans votre environnement, utilisez les étapes manuelles décrites ci-dessous.

---

## 🎯 **Introduction**

Ce guide vous explique comment configurer **complètement** le repository GitHub pour **Agent World** afin de :

- **Organiser le backlog** (labels, milestones, projects).
- **Automatiser les workflows** (CI/CD, releases).
- **Sécuriser le repository** (branches protégées, secrets).
- **Suivre les métriques** (Insights, dépendances).

---

## 📦 **Structure du Repository**

Voici la structure **recommandée** pour le repository :

```
agent-world/
├── .github/
│   ├── ISSUES.md          # Template pour les issues
│   ├── PROJECT.md         # Ce fichier (guide de configuration)
│   ├── workflows/          # Workflows GitHub Actions
│   │   ├── ci.yml          # CI (tests, lint, build)
│   │   ├── release.yml     # Release automatique
│   │   └── docs.yml        # Génération de la documentation
│   └── templates/          # Templates pour PR/Issues
│       ├── pull-request.md
│       └── issue.md
│
├── BACKLOG.md             # Backlog produit complet
├── ROADMAP.md             # Roadmap et timeline
├── CHANGELOG.md           # Historique des versions
├── CONTRIBUTING.md        # Guide de contribution
├── CODE_OF_CONDUCT.md     # Code de conduite
├── INSTALL.md             # Guide d'installation
├── README.md              # Documentation principale
├── LICENSE                # Licence MIT
├── .gitignore             # Fichiers à exclure
├── requirements.txt       # Dépendances Python
├── package.json           # Dépendances Node.js (si frontend)
└── src/                  # Code source
    ├── backend/           # Backend (Flask/FastAPI)
    ├── frontend/          # Frontend (React/Next.js)
    └── cli/               # Interface CLI
```

---

## 🏷️ **Configuration des Labels**

### **🔹 Liste Complète des Labels**

Voici la liste des **20+ labels** à créer pour organiser les issues et pull requests :

#### **1. Labels par Type**

| **Nom**               | **Description**                          | **Couleur**       | **Exemple d'utilisation**          |
|-----------------------|------------------------------------------|-------------------|------------------------------------|
| `bug`                 | Bug à corriger.                          | `#d73a4a` (rouge) | Issue : "Le dashboard ne s'affiche pas" |
| `enhancement`         | Nouvelle fonctionnalité.                | `#0075ca` (bleu)  | Issue : "Ajouter un thème sombre" |
| `question`            | Question ou demande de clarification.      | `#cc317c` (rose)  | Issue : "Comment configurer PostgreSQL ?" |
| `documentation`       | Mise à jour de la documentation.        | `#0075ca` (bleu)  | Issue : "Mettre à jour le README" |
| `technical-debt`      | Tâche technique (refactorisation, etc.). | `#f9c514` (jaune) | Issue : "Optimiser les requêtes SQL" |
| `design`              | Proposition ou tâche liée au design.     | `#a4a9ad` (gris)  | Issue : "Nouveau design pour le dashboard" |

#### **2. Labels par Priorité**

| **Nom**               | **Description**                          | **Couleur**       | **Exemple d'utilisation**          |
|-----------------------|------------------------------------------|-------------------|------------------------------------|
| `priority: high`      | Priorité élevée (P0 - Must Have).        | `#d73a4a` (rouge) | Issue : "Corriger le bug critique" |
| `priority: medium`    | Priorité moyenne (P1 - Should Have).     | `#f9c514` (jaune) | Issue : "Ajouter une fonctionnalité" |
| `priority: low`       | Priorité basse (P2 - Could Have).        | `#0e8a16` (vert)  | Issue : "Amélioration mineure" |

#### **3. Labels par Épic**

| **Nom**               | **Description**                          | **Couleur**       | **Exemple d'utilisation**          |
|-----------------------|------------------------------------------|-------------------|------------------------------------|
| `epic: mvp`           | Épic 1 : MVP.                            | `#0075ca` (bleu)  | Issue : "Initialisation du projet" |
| `epic: vs-code`       | Épic 2 : Intégration VS Code.            | `#0075ca` (bleu)  | Issue : "Ouverture du dashboard VS Code" |
| `epic: files`         | Épic 3 : Gestion des Fichiers.           | `#0075ca` (bleu)  | Issue : "Dossier de sortie personnalisé" |
| `epic: history`       | Épic 4 : Historique et Versioning.       | `#0075ca` (bleu)  | Issue : "Historique des agents" |
| `epic: templates`     | Épic 5 : Templates et Personnalisation. | `#0075ca` (bleu)  | Issue : "Création de templates" |
| `epic: collaboration` | Épic 6 : Collaboration.                  | `#0075ca` (bleu)  | Issue : "Invitation d'utilisateurs" |
| `epic: integrations`  | Épic 7 : Intégrations Externes.          | `#0075ca` (bleu)  | Issue : "Intégration GitHub" |
| `epic: performance`   | Épic 8 : Performance et Scalabilité.     | `#0075ca` (bleu)  | Issue : "Optimisation des requêtes API" |
| `epic: ux`           | Épic 9 : Expérience Utilisateur.         | `#0075ca` (bleu)  | Issue : "Design System" |
| `epic: security`      | Épic 10 : Sécurité et Conformité.        | `#0075ca` (bleu)  | Issue : "Authentification 2FA" |

#### **4. Labels par Composant**

| **Nom**               | **Description**                          | **Couleur**       | **Exemple d'utilisation**          |
|-----------------------|------------------------------------------|-------------------|------------------------------------|
| `component: backend`  | Backend (Flask/FastAPI).                 | `#0075ca` (bleu)  | Issue : "Bug dans l'API" |
| `component: frontend` | Frontend (React/Next.js).                | `#0075ca` (bleu)  | Issue : "Bug dans l'UI" |
| `component: api`      | API REST/GraphQL.                        | `#0075ca` (bleu)  | Issue : "Ajouter un endpoint" |
| `component: cli`      | Interface en ligne de commande.           | `#0075ca` (bleu)  | Issue : "Améliorer le CLI" |
| `component: vs-code`  | Extension VS Code.                       | `#0075ca` (bleu)  | Issue : "Bug dans l'extension VS Code" |
| `component: database` | Base de données (PostgreSQL, MongoDB).   | `#0075ca` (bleu)  | Issue : "Optimiser les requêtes" |
| `component: models`   | Modèles IA (Mistral, OpenAI, etc.).      | `#0075ca` (bleu)  | Issue : "Ajouter un nouveau modèle" |

#### **5. Labels par Statut**

| **Nom**               | **Description**                          | **Couleur**       | **Exemple d'utilisation**          |
|-----------------------|------------------------------------------|-------------------|------------------------------------|
| `status: to do`       | À faire.                                 | `#fbca04` (orange)| Issue : "Fonctionnalité non démarrée" |
| `status: in progress` | En cours.                                | `#0075ca` (bleu)  | Issue : "Fonctionnalité en développement" |
| `status: review`      | En revue.                                | `#f9c514` (jaune) | PR : "Pull Request en attente de revue" |
| `status: done`        | Terminé.                                | `#0e8a16` (vert)  | Issue : "Fonctionnalité implémentée" |
| `status: blocked`     | Bloqué.                                 | `#d73a4a` (rouge) | Issue : "Fonctionnalité bloquée par une dépendance" |

#### **6. Labels pour les Pull Requests**

| **Nom**               | **Description**                          | **Couleur**       | **Exemple d'utilisation**          |
|-----------------------|------------------------------------------|-------------------|------------------------------------|
| `pr: needs-review`    | Pull Request en attente de revue.         | `#f9c514` (jaune) | PR : "Ajout d'une nouvelle fonctionnalité" |
| `pr: approved`        | Pull Request approuvée.                  | `#0e8a16` (vert)  | PR : "Ready to merge" |
| `pr: changes-requested` | Pull Request avec des changements demandés. | `#d73a4a` (rouge) | PR : "Modifications nécessaires" |
| `pr: work-in-progress` | Pull Request en cours de développement. | `#fbca04` (orange)| PR : "WIP: Nouvelle fonctionnalité" |

---

### **🔹 Comment Créer les Labels ?**

1. Allez dans **Settings > Labels** de votre repository.
2. Cliquez sur **New Label**.
3. Remplissez :
   - **Label name** : Nom du label (ex: `bug`).
   - **Description** : Description du label (ex: "Bug à corriger").
   - **Color** : Couleur au format hexadécimal (ex: `#d73a4a`).
4. Cliquez sur **Create Label**.

> **⚠️ Astuce** : Vous pouvez utiliser le **bulk edit** pour créer plusieurs labels en une seule fois.

---

## 🎯 **Configuration des Milestones**

### **🔹 Liste des Milestones**

Voici les **6 milestones** à créer pour organiser les sprints et les versions :

| **Nom**               | **Description**                          | **Date de Livraison** | **Version** | **Issues Associées**          |
|-----------------------|------------------------------------------|-----------------------|-------------|--------------------------------|
| **MVP**               | Épic 1 : Minimum Viable Product.         | 06 août 2026          | v0.1.0      | US-001 à US-010                |
| **VS Code**           | Épic 2 : Intégration VS Code.             | 12 août 2026          | v0.2.0      | US-011 à US-017                |
| **Files**             | Épic 3 : Gestion des Fichiers.            | 19 août 2026          | v0.2.1      | US-018 à US-024                |
| **History**           | Épic 4 : Historique et Versioning.       | 02 septembre 2026     | v0.3.0      | US-025 à US-032                |
| **Templates**         | Épic 5 : Templates et Personnalisation. | 16 septembre 2026     | v0.3.1      | US-033 à US-039                |
| **Collaboration**     | Épic 6 : Collaboration.                  | 30 septembre 2026     | v0.4.0      | US-040 à US-046                |

### **🔹 Comment Créer les Milestones ?**

1. Allez dans **Issues > Milestones**.
2. Cliquez sur **New Milestone**.
3. Remplissez :
   - **Title** : Nom du milestone (ex: `VS Code`).
   - **Description** : Description du milestone (ex: "Intégration VS Code - Version v0.2.0").
   - **Due date** : Date de livraison (ex: `2026-08-12`).
   - **State** : `Open` (par défaut).
4. Cliquez sur **Create Milestone**.

---

## 📋 **Configuration des Projects**

### **🔹 Créer un Tableau Kanban**

1. Allez dans **Projects > New Project**.
2. Sélectionnez **Board** (tableau Kanban).
3. Donnez un nom au projet : **"Agent World Backlog"**.
4. Ajoutez les **colonnes** suivantes :
   - **To Do** : Issues non démarrées.
   - **In Progress** : Issues en cours de développement.
   - **Review** : Pull Requests en attente de revue.
   - **Done** : Issues terminées.
   - **Blocked** : Issues bloquées.

5. **Personnalisez les colonnes** :
   - Ajoutez une **description** à chaque colonne.
   - Définissez des **règles d'automatisation** (ex: déplacer automatiquement les issues avec le label `status: done` dans la colonne **Done**).

### **🔹 Ajouter des Issues au Project**

1. Allez dans **Issues**.
2. Sélectionnez les issues à ajouter au projet.
3. Cliquez sur **Projects** dans la barre latérale droite.
4. Sélectionnez **"Agent World Backlog"**.
5. Glissez-déposez les issues dans les colonnes appropriées.

---

## ⚙️ **Configuration de la CI/CD**

### **🔹 Workflows GitHub Actions**

Créez les workflows suivants dans `.github/workflows/` :

#### **1. Workflow CI (Continuous Integration)**

**Fichier** : `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          pip install flake8 black isort
          flake8 .
          black --check .
          isort --check-only .

      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          file: ./coverage.xml

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: goupiljeremy/agent-world:latest,goupiljeremy/agent-world:${{ github.sha }}
```

#### **2. Workflow Release**

**Fichier** : `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest

      - name: Build Docker Image
        run: |
          docker build -t goupiljeremy/agent-world:${{ github.ref_name }} .
          docker push goupiljeremy/agent-world:${{ github.ref_name }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          name: ${{ github.ref_name }}
          body: |
            ## 📌 Changelog
            - [Voir le CHANGELOG.md](https://github.com/GoupilJeremy/agent-world/blob/${{ github.ref_name }}/CHANGELOG.md)
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### **3. Workflow Documentation**

**Fichier** : `.github/workflows/docs.yml`

```yaml
name: Docs

on:
  push:
    branches: [main]
    paths:
      - "**.md"
      - "docs/**"

jobs:
  build-docs:
    name: Build Documentation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install mkdocs mkdocs-material

      - name: Build docs
        run: mkdocs build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

---

### **🔹 Secrets GitHub**

Pour que les workflows fonctionnent, vous devez configurer les **secrets** suivants dans **Settings > Secrets > Actions** :

| **Nom**               | **Description**                          | **Exemple**                          |
|-----------------------|------------------------------------------|--------------------------------------|
| `CODECOV_TOKEN`       | Token pour Codecov (couverture de code). | `votre_token_codecov`               |
| `DOCKER_HUB_USERNAME` | Nom d'utilisateur Docker Hub.           | `goupiljeremy`                       |
| `DOCKER_HUB_TOKEN`    | Token Docker Hub.                       | `votre_token_docker`                |
| `GITHUB_TOKEN`        | Token GitHub (pour les releases).       | `ghp_votre_token`                   |

---

## 🔒 **Configuration de la Sécurité**

### **🔹 Branches Protégées**

1. Allez dans **Settings > Branches**.
2. Cliquez sur **Add branch protection rule**.
3. Remplissez :
   - **Branch name pattern** : `main` (et éventuellement `develop`).
   - **Require a pull request before merging** : ✅
   - **Require approvals** : 1 (ou 2 pour plus de sécurité).
   - **Dismiss stale pull request approvals when new commits are pushed** : ✅
   - **Require status checks to pass before merging** : ✅
     - Sélectionnez les workflows CI requis (ex: `CI`).
   - **Include administrators** : ✅ (pour appliquer les règles aux admins).
   - **Restrict who can push to matching branches** : ✅
     - Sélectionnez les utilisateurs ou équipes autorisés (ex: `GoupilJeremy`).

### **🔹 Règles de Sécurité**

1. Allez dans **Settings > Security & analysis**.
2. Activez les options suivantes :
   - **Dependabot alerts** : ✅ (pour les mises à jour de sécurité).
   - **Dependabot security updates** : ✅ (pour les corrections automatiques).
   - **Secret scanning** : ✅ (pour détecter les secrets commités).
   - **Secret scanning push protection** : ✅ (pour bloquer les pushes avec des secrets).

### **🔹 CODEOWNERS**

Créez un fichier `.github/CODEOWNERS` pour définir les responsables des fichiers :

```
# CODEOWNERS

# Backend
backend/ @GoupilJeremy

# Frontend
frontend/ @GoupilJeremy

# Documentation
*.md @GoupilJeremy

# Workflows CI/CD
.github/workflows/ @GoupilJeremy

# Tout le reste
* @GoupilJeremy
```

---

## 📊 **Configuration des Insights**

### **🔹 GitHub Insights**

1. Allez dans **Insights** > **Pulse** pour voir l'activité du repository.
2. **Traffic** : Voir les visites sur le repository.
3. **Contributors** : Voir la liste des contributeurs.
4. **Dependency Graph** : Voir les dépendances et les vulnérabilités.

### **🔹 Dependabot**

1. Allez dans **Settings > Security & analysis > Dependabot**.
2. Activez **Dependabot** pour :
   - **Python** (pip).
   - **JavaScript** (npm).
   - **Docker**.n3. Configurez les **mises à jour automatiques** :
   - **Schedule** : Daily.
   - **Open pull requests** : ✅
   - **Auto-merge** : ✅ (pour les mises à jour de patch).

---

## 🤖 **Configuration des Bots**

### **🔹 Bots Recommandés**

| **Bot**               | **Description**                          | **Lien**                                  | **Configuration**                          |
|-----------------------|------------------------------------------|------------------------------------------|------------------------------------------|
| **Dependabot**        | Mises à jour de dépendances.             | [Dependabot](https://dependabot.com/)   | Activé via GitHub Settings.             |
| **Codecov**           | Couverture de code.                      | [Codecov](https://codecov.io/)          | Ajoutez `CODECOV_TOKEN` dans Secrets.     |
| **Stale**             | Fermeture des issues/PR inactives.       | [Stale](https://github.com/apps/stale)  | Configurez via `.github/stale.yml`.      |
| **Welcome**           | Message de bienvenue pour les nouveaux contributeurs. | [Welcome](https://github.com/apps/welcome) | Configurez via `.github/welcome.yml`. |

### **🔹 Configuration de Stale**

**Fichier** : `.github/stale.yml`

```yaml
# Configuration pour le bot Stale

# Nombre de jours avant qu'une issue/PR soit marquée comme stale
stale_days: 30

# Nombre de jours avant qu'une issue/PR stale soit fermée
close_days: 7

# Issues à ignorer (ex: pinned, milestoned)
exempt_issues:
  - labels:
      - "pinned"
      - "security"

# PRs à ignorer
exempt_prs:
  - labels:
      - "work-in-progress"

# Message pour les issues stale
stale_issue_message: |
  Cette issue n'a pas eu d'activité depuis 30 jours. Elle sera fermée dans 7 jours si aucune mise à jour n'est apportée.

# Message pour les PRs stale
stale_pr_message: |
  Cette pull request n'a pas eu d'activité depuis 30 jours. Elle sera fermée dans 7 jours si aucune mise à jour n'est apportée.

# Label à ajouter aux issues/PRs stale
stale_label: "stale"
```

### **🔹 Configuration de Welcome**

**Fichier** : `.github/welcome.yml`

```yaml
# Configuration pour le bot Welcome

# Message de bienvenue pour les nouveaux contributeurs
welcome_message: |
  🎉 Bienvenue dans **Agent World** ! Merci pour votre contribution.
  
  Voici quelques ressources pour bien démarrer :
  - [Backlog](https://github.com/GoupilJeremy/agent-world/blob/main/BACKLOG.md)
  - [Contributing](https://github.com/GoupilJeremy/agent-world/blob/main/CONTRIBUTING.md)
  - [Roadmap](https://github.com/GoupilJeremy/agent-world/blob/main/ROADMAP.md)
  
  N'hésitez pas à poser des questions dans [Discussions](https://github.com/GoupilJeremy/agent-world/discussions) !

# Message pour les nouvelles issues
issue_message: |
  Merci d'avoir ouvert une issue ! 🎉
  
  Pour nous aider à résoudre votre problème, veuillez :
  - Utiliser un [template](https://github.com/GoupilJeremy/agent-world/blob/main/.github/ISSUES.md).
  - Ajouter des **labels** appropriés.
  - Fournir autant de **détails** que possible.

# Message pour les nouvelles PRs
pr_message: |
  Merci d'avoir ouvert une pull request ! 🎉
  
  Pour que votre PR soit mergée rapidement, veuillez :
  - Suivre les [conventions de code](https://github.com/GoupilJeremy/agent-world/blob/main/CONTRIBUTING.md#conventions-de-code).
  - Ajouter des **tests** pour vos changements.
  - Mettre à jour la **documentation** si nécessaire.
```

---

## 📜 **Checklist de Configuration**

Voici une **checklist** pour configurer complètement le repository :

### **✅ Configuration de Base**
- [ ] Repository GitHub créé (`GoupilJeremy/agent-world`).
- [ ] Fichiers de base ajoutés (`README.md`, `LICENSE`, `.gitignore`).
- [ ] Structure du repository validée.

### **🏷️ Labels**
- [ ] Labels par **type** créés (`bug`, `enhancement`, `question`, etc.).
- [ ] Labels par **priorité** créés (`priority: high`, `priority: medium`, `priority: low`).
- [ ] Labels par **épic** créés (`epic: mvp`, `epic: vs-code`, etc.).
- [ ] Labels par **composant** créés (`component: backend`, `component: frontend`, etc.).
- [ ] Labels par **statut** créés (`status: to do`, `status: in progress`, etc.).
- [ ] Labels pour les **PRs** créés (`pr: needs-review`, `pr: approved`, etc.).

### **🎯 Milestones**
- [ ] Milestone **MVP** créé (v0.1.0 - 06 août 2026).
- [ ] Milestone **VS Code** créé (v0.2.0 - 12 août 2026).
- [ ] Milestone **Files** créé (v0.2.1 - 19 août 2026).
- [ ] Milestone **History** créé (v0.3.0 - 02 septembre 2026).
- [ ] Milestone **Templates** créé (v0.3.1 - 16 septembre 2026).
- [ ] Milestone **Collaboration** créé (v0.4.0 - 30 septembre 2026).

### **📋 Projects**
- [ ] Project **"Agent World Backlog"** créé (type: Board).
- [ ] Colonnes **To Do**, **In Progress**, **Review**, **Done**, **Blocked** ajoutées.
- [ ] Issues du **Sprint 0** ajoutées au project.

### **⚙️ CI/CD**
- [ ] Workflow **CI** créé (`.github/workflows/ci.yml`).
- [ ] Workflow **Release** créé (`.github/workflows/release.yml`).
- [ ] Workflow **Docs** créé (`.github/workflows/docs.yml`).
- [ ] Secrets GitHub configurés (`CODECOV_TOKEN`, `DOCKER_HUB_USERNAME`, etc.).

### **🔒 Sécurité**
- [ ] Branche **`main`** protégée.
- [ ] Règles de sécurité activées (Dependabot, Secret Scanning).
- [ ] Fichier **CODEOWNERS** créé.

### **🤖 Bots**
- [ ] Bot **Dependabot** activé.
- [ ] Bot **Codecov** configuré.
- [ ] Bot **Stale** configuré (`.github/stale.yml`).
- [ ] Bot **Welcome** configuré (`.github/welcome.yml`).

### **📊 Insights**
- [ ] GitHub Insights activés.
- [ ] Dependabot configuré pour les mises à jour automatiques.

### **📝 Documentation**
- [ ] Fichier **BACKLOG.md** ajouté.
- [ ] Fichier **ROADMAP.md** ajouté.
- [ ] Fichier **CHANGELOG.md** ajouté.
- [ ] Fichier **CONTRIBUTING.md** ajouté.
- [ ] Fichier **CODE_OF_CONDUCT.md** ajouté.
- [ ] Fichier **INSTALL.md** ajouté.
- [ ] Fichier **`.github/ISSUES.md`** ajouté.
- [ ] Fichier **`.github/PROJECT.md`** ajouté.

---

## 🎉 **Prochaines Étapes**

Une fois la configuration terminée, vous pouvez :

1. **Créer les issues du Sprint 0** :
   - US-011 : Ouverture du dashboard VS Code.
   - US-012 : Thème automatique VS Code.
   - US-013 : Ouverture des fichiers dans VS Code.
   - US-018 : Dossier de sortie personnalisé.
   - US-019 : Noms de fichiers intelligents.

2. **Inviter des contributeurs** :
   - Allez dans **Settings > Collaborators**.
   - Ajoutez les utilisateurs avec le rôle **Write** ou **Admin**.

3. **Configurer les Discussions** :
   - Allez dans **Discussions** et créez des catégories :
     - **General** : Questions générales.
     - **Help** : Demande d'aide.
     - **Ideas** : Propositions de fonctionnalités.
     - **Show and Tell** : Partage de projets utilisant Agent World.

4. **Configurer les Pages GitHub** (pour la documentation) :
   - Allez dans **Settings > Pages**.
   - Sélectionnez **GitHub Actions** comme source.
   - Choisissez le workflow **docs.yml**.

5. **Annoncez le Projet** :
   - Partagez le repository sur les réseaux sociaux.
   - Écrivez un article de blog ou un post LinkedIn.
   - Soumettez le projet à des plateformes comme [Product Hunt](https://www.producthunt.com/).

---

## 🔗 **Ressources**

- [GitHub Docs](https://docs.github.com/) : Documentation officielle de GitHub.
- [GitHub Actions Docs](https://docs.github.com/en/actions) : Documentation des workflows.
- [GitHub Community Forum](https://github.community/) : Forum d'entraide.
- [Agent World Backlog](https://github.com/GoupilJeremy/agent-world/blob/main/BACKLOG.md) : Détail des fonctionnalités.
- [Agent World Roadmap](https://github.com/GoupilJeremy/agent-world/blob/main/ROADMAP.md) : Timeline et objectifs.

---

## 🙏 **Remerciements**

Merci d'avoir configuré **Agent World** ! 🎉

Avec cette configuration, votre repository est prêt à :
- **Organiser le backlog** de manière professionnelle.
- **Automatiser les workflows** (CI/CD, releases).
- **Sécuriser le code** et les contributions.
- **Suivre les métriques** et l'activité du projet.

Si vous avez des questions, n'hésitez pas à consulter la [documentation](https://github.com/GoupilJeremy/agent-world) ou à ouvrir une **issue**.

---

*Document généré le 06 août 2026. Dernière mise à jour : [DATE]*
