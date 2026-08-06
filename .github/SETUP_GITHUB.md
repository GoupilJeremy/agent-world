# 🚀 **Guide de Configuration GitHub pour Agent World**
*Comment configurer le backlog, les issues, et les projets GitHub*

---

## 📌 **Résumé**
Ce guide vous explique comment configurer **GitHub** pour organiser le projet **Agent World** avec :
- **Labels** (20+ labels pour catégoriser les issues/PRs).
- **Milestones** (6 milestones pour les épics).
- **Projet Kanban** (tableau pour suivre le backlog).
- **Issues** (User Stories du Sprint 0).

---

## 📁 **Fichiers Générés**
Les scripts et fichiers suivants ont été créés dans `/workspace/GoupilJeremy__agent-world/` :

### **Scripts Bash** (à exécuter manuellement)
| **Fichier** | **Description** | **Commande** |
|-------------|----------------|--------------|
| `scripts/create_github_labels.sh` | Crée les 28 labels GitHub. | `bash scripts/create_github_labels.sh` |
| `scripts/create_github_milestones.sh` | Crée les 6 milestones. | `bash scripts/create_github_milestones.sh` |
| `scripts/create_github_project.sh` | Crée le projet Kanban. | `bash scripts/create_github_project.sh` |
| `scripts/create_sprint0_issues.sh` | Crée les 5 issues du Sprint 0. | `bash scripts/create_sprint0_issues.sh` |

### **Fichiers de Configuration**
| **Fichier** | **Description** |
|-------------|----------------|
| `.github/labels.json` | Liste complète des labels au format JSON (pour import manuel). |
| `.github/sprint0_issues.csv` | Liste des issues du Sprint 0 au format CSV. |

---

## 🛠 **Étapes de Configuration**

### **1️⃣ Créer les Labels**
#### **Option A : Utiliser le script Bash**
```bash
cd /workspace/GoupilJeremy__agent-world
bash scripts/create_github_labels.sh
```
> ⚠️ **Note** : Si les appels API sont bloqués, utilisez l'option B.

#### **Option B : Créer manuellement via l'UI GitHub**
1. Allez dans **Settings > Labels** de votre repository.
2. Cliquez sur **New Label** pour chaque label.
3. Utilisez les informations du fichier [`.github/labels.json`](.github/labels.json).

#### **Liste des Labels à Créer**
| **Type** | **Nom** | **Couleur** | **Description** |
|----------|---------|-------------|-----------------|
| Type | `bug` | `#d73a4a` | Bug à corriger |
| Type | `enhancement` | `#0075ca` | Nouvelle fonctionnalité |
| Type | `question` | `#cc317c` | Question ou demande de clarification |
| Type | `documentation` | `#0075ca` | Mise à jour de la documentation |
| Type | `technical-debt` | `#f9c514` | Tâche technique |
| Type | `design` | `#a4a9ad` | Proposition de design |
| Priorité | `priority: high` | `#d73a4a` | P0 (Must Have) |
| Priorité | `priority: medium` | `#f9c514` | P1 (Should Have) |
| Priorité | `priority: low` | `#0e8a16` | P2 (Could Have) |
| Épic | `epic: mvp` | `#0075ca` | Épic 1 : MVP |
| Épic | `epic: vs-code` | `#0075ca` | Épic 2 : Intégration VS Code |
| Épic | `epic: files` | `#0075ca` | Épic 3 : Gestion des Fichiers |
| Épic | `epic: history` | `#0075ca` | Épic 4 : Historique |
| Épic | `epic: templates` | `#0075ca` | Épic 5 : Templates |
| Épic | `epic: collaboration` | `#0075ca` | Épic 6 : Collaboration |
| Épic | `epic: integrations` | `#0075ca` | Épic 7 : Intégrations |
| Épic | `epic: performance` | `#0075ca` | Épic 8 : Performance |
| Épic | `epic: ux` | `#0075ca` | Épic 9 : UX |
| Épic | `epic: security` | `#0075ca` | Épic 10 : Sécurité |
| Composant | `component: backend` | `#0075ca` | Backend (Flask/FastAPI) |
| Composant | `component: frontend` | `#0075ca` | Frontend (React/Next.js) |
| Composant | `component: api` | `#0075ca` | API REST/GraphQL |
| Composant | `component: cli` | `#0075ca` | Interface CLI |
| Composant | `component: vs-code` | `#0075ca` | Extension VS Code |
| Composant | `component: database` | `#0075ca` | Base de données |
| Composant | `component: models` | `#0075ca` | Modèles IA |
| Statut | `status: to do` | `#fbca04` | À faire |
| Statut | `status: in progress` | `#0075ca` | En cours |
| Statut | `status: review` | `#f9c514` | En revue |
| Statut | `status: done` | `#0e8a16` | Terminé |
| Statut | `status: blocked` | `#d73a4a` | Bloqué |
| PR | `pr: needs-review` | `#f9c514` | PR en attente de revue |
| PR | `pr: approved` | `#0e8a16` | PR approuvée |
| PR | `pr: changes-requested` | `#d73a4a` | PR avec changements demandés |
| PR | `pr: work-in-progress` | `#fbca04` | PR en cours |

---

### **2️⃣ Créer les Milestones**
#### **Option A : Utiliser le script Bash**
```bash
bash scripts/create_github_milestones.sh
```

#### **Option B : Créer manuellement via l'UI GitHub**
1. Allez dans **Issues > Milestones**.
2. Cliquez sur **New Milestone** pour chaque milestone.

| **Nom** | **Description** | **Date de Livraison** | **Version** |
|---------|----------------|-----------------------|-------------|
| MVP | Épic 1 : Minimum Viable Product | 06 août 2026 | v0.1.0 |
| VS Code | Épic 2 : Intégration VS Code | 12 août 2026 | v0.2.0 |
| Files | Épic 3 : Gestion des Fichiers | 19 août 2026 | v0.2.1 |
| History | Épic 4 : Historique et Versioning | 02 septembre 2026 | v0.3.0 |
| Templates | Épic 5 : Templates et Personnalisation | 16 septembre 2026 | v0.3.1 |
| Collaboration | Épic 6 : Collaboration | 30 septembre 2026 | v0.4.0 |

---

### **3️⃣ Créer le Projet Kanban**
#### **Option A : Utiliser le script Bash**
```bash
bash scripts/create_github_project.sh
```

#### **Option B : Créer manuellement via l'UI GitHub**
1. Allez dans **Projects > New Project**.
2. Sélectionnez **Board** (tableau Kanban).
3. Donnez le nom : **"Agent World Backlog"**.
4. Ajoutez les colonnes :
   - **To Do**
   - **In Progress**
   - **Review**
   - **Done**
   - **Blocked**

---

### **4️⃣ Créer les Issues du Sprint 0**
#### **Option A : Utiliser le script Bash**
```bash
bash scripts/create_sprint0_issues.sh
```

#### **Option B : Créer manuellement via l'UI GitHub**
Utilisez le fichier [`.github/sprint0_issues.csv`](.github/sprint0_issues.csv) comme référence pour créer les 5 issues suivantes :

| **ID** | **Titre** | **Labels** | **Milestone** | **Estimation** |
|--------|-----------|------------|---------------|----------------|
| US-011 | `[FEAT] [VS Code] Ouverture du dashboard VS Code` | `enhancement,epic: vs-code,component: vs-code,priority: high,status: to do` | VS Code | 8h |
| US-012 | `[FEAT] [VS Code] Thème automatique VS Code` | `enhancement,epic: vs-code,component: vs-code,priority: high,status: to do` | VS Code | 4h |
| US-013 | `[FEAT] [VS Code] Ouverture des fichiers dans VS Code` | `enhancement,epic: vs-code,component: vs-code,priority: high,status: to do` | VS Code | 3h |
| US-018 | `[FEAT] [Files] Dossier de sortie personnalisé` | `enhancement,epic: files,component: backend,priority: high,status: to do` | Files | 2h |
| US-019 | `[FEAT] [Files] Noms de fichiers intelligents` | `enhancement,epic: files,component: backend,priority: high,status: to do` | Files | 4h |

#### **Exemple de corps d'issue (US-011)**
```markdown
## 🎯 Description
Créer un dashboard pour visualiser les agents directement depuis VS Code.

---

## ✅ Critères d'Acceptation
- [ ] Extension VS Code créée
- [ ] Affichage des agents dans le dashboard
- [ ] Navigation basique entre les agents

---

## 📌 Détails
- **Épic** : [Épic 2 : Intégration VS Code](BACKLOG.md#épic-2--intégration-vs-code)
- **User Story** : US-011
- **Estimation** : 8h
- **Priorité** : P0 (Must Have)
```

---

### **5️⃣ Lier les Issues au Projet Kanban**
1. Allez dans **Issues**.
2. Sélectionnez les issues créées (US-011 à US-019).
3. Dans la barre latérale droite, cliquez sur **Projects**.
4. Sélectionnez **"Agent World Backlog"**.
5. Glissez-déposez les issues dans la colonne **To Do**.

---

## 📊 **Résultat Attendu**
Une fois toutes les étapes terminées, vous aurez :
- ✅ **28 labels** pour catégoriser les issues/PRs.
- ✅ **6 milestones** pour les épics.
- ✅ **1 projet Kanban** avec 5 colonnes.
- ✅ **5 issues** pour le Sprint 0 (US-011 à US-019).

---

## 🔗 **Liens Utiles**
- [Repository GitHub](https://github.com/GoupilJeremy/agent-world)
- [Backlog Complet](BACKLOG.md)
- [Roadmap](ROADMAP.md)
- [Documentation GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects)

---

## 💡 **Conseils**
1. **Automatisez** : Utilisez les scripts Bash si possible pour gagner du temps.
2. **Vérifiez** : Après chaque étape, vérifiez que les éléments ont bien été créés.
3. **Personnalisez** : Adaptez les labels/milestones selon vos besoins.
4. **Collaborez** : Invitez votre équipe à contribuer via **Settings > Collaborators**.

---

## ❓ **FAQ**
### **Pourquoi les scripts Bash ne fonctionnent-ils pas ?**
Si vous voyez l'erreur `Mutating GitHub API calls are not allowed`, c'est que l'environnement actuel ne permet pas les modifications via l'API GitHub. Dans ce cas, utilisez les **options manuelles** (UI GitHub).

### **Comment importer les labels en masse ?**
GitHub ne propose pas d'import natif pour les labels. Vous devez soit :
- Utiliser le script Bash.
- Créer les labels manuellement via l'UI.
- Utiliser un outil tiers comme [github-label-sync](https://github.com/micnncim/action-label-sync).

### **Comment ajouter des issues à un projet existant ?**
1. Allez dans l'issue.
2. Dans la barre latérale, cliquez sur **Projects**.
3. Sélectionnez le projet souhaité.

---

## 🎉 **Prochaines Étapes**
1. **Exécutez les scripts** ou suivez les étapes manuelles.
2. **Vérifiez** que tout est bien configuré.
3. **Commencez le Sprint 0** en assignant les issues à votre équipe.
4. **Suivez l'avancement** via le projet Kanban.

---

*Document généré le 06 août 2026. Dernière mise à jour : [DATE]*
