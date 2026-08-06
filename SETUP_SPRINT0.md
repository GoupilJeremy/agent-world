# 🚀 Configuration du Sprint 0 pour Agent World

Ce guide vous permet de configurer rapidement votre repository GitHub avec tous les éléments nécessaires pour démarrer le **Sprint 0** du projet Agent World.

## 📌 Résumé Rapide

Pour configurer **TOUT** en une seule commande :

```bash
# Méthode 1: Avec votre token GitHub
GITHUB_TOKEN=votre_token_ici python3 scripts/setup_github_complete.py

# Méthode 2: Le script vous demandera votre token
python3 scripts/setup_github_complete.py
```

**Résultat :** 28 labels + 6 milestones + 1 projet Kanban + 5 issues du Sprint 0

---

## 🔧 Prérequis

### 1. Personal Access Token GitHub

Vous avez besoin d'un **token GitHub** avec les permissions :
- ✅ `repo` - Accès complet (pour labels, milestones, issues)
- ✅ `project` - Lecture/Écriture (pour le projet Kanban)

**Comment créer votre token :**

1. Allez sur [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Cliquez sur **"Generate new token"** (classic)
3. **Token name :** `Agent World Setup`
4. **Expiration :** 30 jours (ou plus)
5. **Permissions :**
   - ☑️ `repo` - Tout cocher
   - ☑️ `project` - Read and write
6. Cliquez sur **"Generate token"**
7. **⚠️ IMPORTANT : Copiez le token immédiatement** (il ne sera plus visible après)

### 2. Python 3 et modules

Vérifiez que vous avez :
```bash
python3 --version  # Doit être >= 3.6
python3 -c "import requests"  # Doit fonctionner
```

Si `requests` n'est pas installé :
```bash
pip3 install requests
```

---

## 🎯 Méthode Recommandée : Script Python Automatique

### Étapes :

```bash
# 1. Naviguez vers votre repository
cd /mnt/c/dev/agent-world/agent-world

# 2. Exécutez le script avec votre token
GITHUB_TOKEN=ghp_votre_token_ici python3 scripts/setup_github_complete.py
```

**Le script va :**
1. ✅ Créer les 28 labels
2. ✅ Créer les 6 milestones
3. ✅ Créer le projet Kanban "Agent World Backlog"
4. ✅ Créer les 5 issues du Sprint 0
5. ✅ Afficher un résumé de ce qui a été créé

### Si vous préférez l'interactif :

```bash
python3 scripts/setup_github_complete.py
# Le script vous demandera votre token
```

---

## 📋 Configuration Manuelle (Alternative)

Si vous ne pouvez pas utiliser les scripts, voici les étapes manuelles :

### 1. Créer les Labels (28)

Allez dans : **Settings > Labels > New Label**

| Catégorie | Nom | Couleur | Description |
|-----------|-----|---------|-------------|
| **Type** | `bug` | `#d73a4a` | Bug à corriger |
| **Type** | `enhancement` | `#0075ca` | Nouvelle fonctionnalité |
| **Type** | `question` | `#cc317c` | Question ou demande |
| **Type** | `documentation` | `#0075ca` | Documentation |
| **Type** | `technical-debt` | `#f9c514` | Tâche technique |
| **Type** | `design` | `#a4a9ad` | Design |
| **Priorité** | `priority: high` | `#d73a4a` | P0 - Must Have |
| **Priorité** | `priority: medium` | `#f9c514` | P1 - Should Have |
| **Priorité** | `priority: low` | `#0e8a16` | P2 - Could Have |
| **Épic** | `epic: mvp` | `#0075ca` | Épic 1 : MVP |
| **Épic** | `epic: vs-code` | `#0075ca` | Épic 2 : VS Code |
| **Épic** | `epic: files` | `#0075ca` | Épic 3 : Fichiers |
| **Épic** | `epic: history` | `#0075ca` | Épic 4 : Historique |
| **Épic** | `epic: templates` | `#0075ca` | Épic 5 : Templates |
| **Épic** | `epic: collaboration` | `#0075ca` | Épic 6 : Collaboration |
| **Épic** | `epic: integrations` | `#0075ca` | Épic 7 : Intégrations |
| **Épic** | `epic: performance` | `#0075ca` | Épic 8 : Performance |
| **Épic** | `epic: ux` | `#0075ca` | Épic 9 : UX |
| **Épic** | `epic: security` | `#0075ca` | Épic 10 : Sécurité |
| **Composant** | `component: backend` | `#0075ca` | Backend |
| **Composant** | `component: frontend` | `#0075ca` | Frontend |
| **Composant** | `component: api` | `#0075ca` | API |
| **Composant** | `component: cli` | `#0075ca` | CLI |
| **Composant** | `component: vs-code` | `#0075ca` | Extension VS Code |
| **Composant** | `component: database` | `#0075ca` | Base de données |
| **Composant** | `component: models` | `#0075ca` | Modèles IA |
| **Statut** | `status: to do` | `#fbca04` | À faire |
| **Statut** | `status: in progress` | `#0075ca` | En cours |
| **Statut** | `status: review` | `#f9c514` | En revue |
| **Statut** | `status: done` | `#0e8a16` | Terminé |
| **Statut** | `status: blocked` | `#d73a4a` | Bloqué |

### 2. Créer les Milestones (6)

Allez dans : **Issues > Milestones > New Milestone**

| Titre | Description | Due Date | Version |
|-------|-------------|----------|---------|
| `MVP` | Épic 1 : Minimum Viable Product | 2026-08-06 | v0.1.0 |
| `VS Code` | Épic 2 : Intégration VS Code | 2026-08-12 | v0.2.0 |
| `Files` | Épic 3 : Gestion des Fichiers | 2026-08-19 | v0.2.1 |
| `History` | Épic 4 : Historique et Versioning | 2026-09-02 | v0.3.0 |
| `Templates` | Épic 5 : Templates et Personnalisation | 2026-09-16 | v0.3.1 |
| `Collaboration` | Épic 6 : Collaboration | 2026-09-30 | v0.4.0 |

### 3. Créer le Projet Kanban

Allez dans : **Projects > New Project > Board**

- **Nom :** `Agent World Backlog`
- **Description :** `Projet Kanban pour organiser le backlog d'Agent World`
- **Colonnes :** To Do, In Progress, Review, Done, Blocked

### 4. Créer les Issues du Sprint 0 (5)

Allez dans : **Issues > New Issue**

**Issue 1 - US-011**
- **Titre :** `[FEAT] [VS Code] Ouverture du dashboard VS Code`
- **Labels :** `enhancement, epic: vs-code, component: vs-code, priority: high, status: to do`
- **Milestone :** `VS Code`
- **Body :** Voir [SETUP_GITHUB.md](.github/SETUP_GITHUB.md#exemple-de-corps-dissue-us-011)

**Issue 2 - US-012**
- **Titre :** `[FEAT] [VS Code] Thème automatique VS Code`
- **Labels :** `enhancement, epic: vs-code, component: vs-code, priority: high, status: to do`
- **Milestone :** `VS Code`

**Issue 3 - US-013**
- **Titre :** `[FEAT] [VS Code] Ouverture des fichiers dans VS Code`
- **Labels :** `enhancement, epic: vs-code, component: vs-code, priority: high, status: to do`
- **Milestone :** `VS Code`

**Issue 4 - US-018**
- **Titre :** `[FEAT] [Files] Dossier de sortie personnalisé`
- **Labels :** `enhancement, epic: files, component: backend, priority: high, status: to do`
- **Milestone :** `Files`

**Issue 5 - US-019**
- **Titre :** `[FEAT] [Files] Noms de fichiers intelligents`
- **Labels :** `enhancement, epic: files, component: backend, priority: high, status: to do`
- **Milestone :** `Files`

### 5. Lier les Issues au Projet

1. Allez dans chaque issue créée
2. Dans la barre latérale droite, cliquez sur **Projects**
3. Sélectionnez **"Agent World Backlog"**
4. Les issues seront automatiquement placées dans la colonne **To Do**

---

## 🎉 Vérification

Pour vérifier que tout est correctement configuré :

```bash
# Compter les labels
curl -s https://api.github.com/repos/GoupilJeremy/agent-world/labels | python3 -c "import sys, json; print(f'Labels: {len(json.load(sys.stdin))}')"

# Compter les milestones  
curl -s https://api.github.com/repos/GoupilJeremy/agent-world/milestones | python3 -c "import sys, json; print(f'Milestones: {len(json.load(sys.stdin))}')"

# Compter les issues
curl -s "https://api.github.com/repos/GoupilJeremy/agent-world/issues?state=all" | python3 -c "import sys, json; print(f'Issues: {len(json.load(sys.stdin))}')"

# Vérifier le projet
curl -s https://api.github.com/repos/GoupilJeremy/agent-world/projects | python3 -c "import sys, json; projects = json.load(sys.stdin); print(f'Projets: {len(projects)}'); print([p['name'] for p in projects])"
```

**Résultat attendu :**
- Labels: 28+
- Milestones: 6
- Issues: 5+
- Projets: 1 (Agent World Backlog)

---

## 📚 Fichiers de Référence

| Fichier | Description |
|---------|-------------|
| `.github/labels.json` | Liste complète des labels au format JSON |
| `.github/sprint0_issues.csv` | Liste des issues du Sprint 0 au format CSV |
| `.github/SETUP_GITHUB.md` | Guide complet de configuration manuelle |
| `scripts/setup_github_complete.py` | Script Python pour tout automatiser |
| `scripts/create_github_*.sh` | Scripts Bash originaux |
| `scripts/README.md` | Documentation des scripts |

---

## 💡 Conseils

1. **Sauvegardez votre token** dans un endroit sécurisé
2. **Vérifiez les permissions** du token avant de commencer
3. **Exécutez le script une fois** - il vérifie si les éléments existent déjà
4. **Utilisez les milestones** pour suivre l'avancement des épics
5. **Utilisez le projet Kanban** pour visualiser le travail en cours

---

## ❓ FAQ

### Le script ne fonctionne pas, que faire ?

1. **Vérifiez votre token** - Assurez-vous qu'il est valide et a les bonnes permissions
2. **Vérifiez le nom du repository** - Il doit être `GoupilJeremy/agent-world`
3. **Vérifiez Python** - `python3 --version` doit fonctionner
4. **Vérifiez le module requests** - `python3 -c "import requests"` doit fonctionner

### Puis-je exécuter le script plusieurs fois ?

Oui ! Le script vérifie si chaque élément existe déjà avant de le créer, donc il est sûr de l'exécuter plusieurs fois.

### Comment désinstaller/configurer à nouveau ?

1. Supprimez manuellement les labels, milestones, projets et issues via l'interface GitHub
2. Réexécutez le script

### Mon token a expiré, que faire ?

1. Créez un nouveau token sur GitHub
2. Réexécutez le script avec le nouveau token

---

## 🎯 Prochaines Étapes

Une fois la configuration terminée :

1. **Assigniez les issues** à votre équipe
2. **Débutez le Sprint 0** en déplaçant les issues vers "In Progress"
3. **Suivez l'avancement** via le projet Kanban
4. **Mettez à jour les statuts** régulièrement

Votre projet Agent World est maintenant prêt pour le développement ! 🚀

---

*Document généré le 06 août 2026*
*Repository: https://github.com/GoupilJeremy/agent-world*