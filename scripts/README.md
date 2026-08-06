# Scripts de Configuration GitHub pour Agent World

Ce dossier contient des scripts pour configurer automatiquement votre repository GitHub avec tous les éléments nécessaires pour le projet Agent World.

## 📋 Contenu

- `create_github_labels.sh` - Crée les 28 labels GitHub (version originale)
- `create_github_milestones.sh` - Crée les 6 milestones (version originale)
- `create_github_project.sh` - Crée le projet Kanban (version originale)
- `create_sprint0_issues.sh` - Crée les 5 issues du Sprint 0 (version originale)
- `create_github_labels_with_auth.sh` - Version améliorée avec gestion de token
- `setup_github_complete.py` - **Script Python complet** pour tout configurer

## 🚀 Configuration Complète

### Méthode Recommandée: Utiliser le script Python

Le script Python est la méthode la plus simple et complète :

```bash
# Méthode 1: Avec variable d'environnement
GITHUB_TOKEN=votre_token_github python3 scripts/setup_github_complete.py

# Méthode 2: Interactive (le script vous demandera le token)
python3 scripts/setup_github_complete.py
```

### Ce que le script va créer:

- ✅ **28 Labels** pour catégoriser les issues et PRs
- ✅ **6 Milestones** pour les épics principaux
- ✅ **1 Projet Kanban** avec 5 colonnes (To Do, In Progress, Review, Done, Blocked)
- ✅ **5 Issues** du Sprint 0 (US-011 à US-019)

## 🔐 Token GitHub requis

Pour exécuter les scripts, vous avez besoin d'un **Personal Access Token (PAT)** GitHub avec les permissions suivantes :

- `repo` - Accès complet aux dépôts (pour créer labels, milestones, issues)
- `project` - Lecture/Écriture pour les projets (pour créer le tableau Kanban)

### Comment créer un token :

1. Allez sur https://github.com/settings/tokens
2. Cliquez sur "Generate new token" (classic)
3. Donnez un nom à votre token (ex: "Agent World Setup")
4. Sélectionnez les permissions :
   - `repo` : cochez tout
   - `project` : cochez "Read and write"
5. Cliquez sur "Generate token"
6. **Copiez le token généré** (il ne sera plus visible après)

## 📝 Configuration Manuelle

Si vous préférez configurer manuellement, voici les fichiers de référence :

- `.github/labels.json` - Liste complète des labels au format JSON
- `.github/sprint0_issues.csv` - Liste des issues du Sprint 0
- `.github/SETUP_GITHUB.md` - Guide complet de configuration manuelle

## 🎯 Résumé des Éléments à Créer

### Labels (28)

**Types :** bug, enhancement, question, documentation, technical-debt, design

**Priorités :** priority: high, priority: medium, priority: low

**Épics :** epic: mvp, epic: vs-code, epic: files, epic: history, epic: templates, epic: collaboration, epic: integrations, epic: performance, epic: ux, epic: security

**Composants :** component: backend, component: frontend, component: api, component: cli, component: vs-code, component: database, component: models

**Statuts :** status: to do, status: in progress, status: review, status: done, status: blocked

**Pull Requests :** pr: needs-review, pr: approved, pr: changes-requested, pr: work-in-progress

### Milestones (6)

| Titre | Description | Date | Version |
|-------|-------------|------|---------|
| MVP | Épic 1 : Minimum Viable Product | 06 août 2026 | v0.1.0 |
| VS Code | Épic 2 : Intégration VS Code | 12 août 2026 | v0.2.0 |
| Files | Épic 3 : Gestion des Fichiers | 19 août 2026 | v0.2.1 |
| History | Épic 4 : Historique et Versioning | 02 septembre 2026 | v0.3.0 |
| Templates | Épic 5 : Templates et Personnalisation | 16 septembre 2026 | v0.3.1 |
| Collaboration | Épic 6 : Collaboration | 30 septembre 2026 | v0.4.0 |

### Projet Kanban

- **Nom :** Agent World Backlog
- **Description :** Projet Kanban pour organiser le backlog d'Agent World
- **Colonnes :** To Do, In Progress, Review, Done, Blocked

### Issues du Sprint 0 (5)

Toutes les issues sont détaillées dans `.github/sprint0_issues.csv` et incluent :

- US-011: [FEAT] [VS Code] Ouverture du dashboard VS Code
- US-012: [FEAT] [VS Code] Thème automatique VS Code
- US-013: [FEAT] [VS Code] Ouverture des fichiers dans VS Code
- US-018: [FEAT] [Files] Dossier de sortie personnalisé
- US-019: [FEAT] [Files] Noms de fichiers intelligents

## 🛠 Dépannage

### Erreur: "Mutating GitHub API calls are not allowed"

Cela signifie que votre environnement actuel ne permet pas les modifications via l'API GitHub. Utilisez le script Python ou configurez manuellement via l'interface GitHub.

### Erreur: "Authentication failed"

Vérifiez que :
1. Votre token est valide
2. Votre token a les permissions nécessaires
3. Votre token n'a pas expiré

### Erreur: "404 Not Found"

Vérifiez que le nom du repository est correct : `GoupilJeremy/agent-world`

## 📚 Documentation Complète

Pour plus de détails, consultez :

- [SETUP_GITHUB.md](../.github/SETUP_GITHUB.md) - Guide complet
- [BACKLOG.md](../BACKLOG.md) - Backlog produit complet
- [ROADMAP.md](../ROADMAP.md) - Feuille de route du projet

## 🎉 Résultat Attendu

Après exécution réussie, vous aurez :
- ✅ 28 labels configurés
- ✅ 6 milestones créés
- ✅ 1 projet Kanban fonctionnel
- ✅ 5 issues du Sprint 0 prêtes à être travaillées

Votre repository sera prêt pour le développement du projet Agent World ! 🚀