# 📝 **Agent World - Template pour les Issues GitHub**
*Modèles pour créer des issues structurées*

---

## 📌 **Table des Matières**
1. [🐛 Template de Bug](#-template-de-bug)
2. [💡 Template de Fonctionnalité](#-template-de-fonctionnalité)
3. [❓ Template de Question](#-template-de-question)
4. [📌 Template de Documentation](#-template-de-documentation)
5. [🔧 Template de Tâche Technique](#-template-de-tâche-technique)
6. [🎨 Template de Design](#-template-de-design)

---

## 🐛 **Template de Bug**

**Titre** : `[BUG] [Composant] Description du bug`
**Exemple** : `[BUG] [VS Code] Le dashboard ne s'affiche pas`

**Labels** : `bug`, `priority: high/medium/low`, `component: [nom]`

**Corps** :
```markdown
## 🐛 Description du Bug
Une description **claire et concise** du bug.

---

## 🔍 Étapes pour Reproduire
1. Allez sur '...'
2. Cliquez sur '...'
3. Faites '...'
4. Le bug apparaît : **Comportement inattendu**

---

## ✅ Comportement Attendu
Ce qui **devrait** se passer.

---

## ❌ Comportement Actuel
Ce qui **se passe réellement** (avec captures d'écran ou logs si possible).

---

## 📸 Captures d'Écran / Logs
```
[Ajoutez des captures d'écran ou des extraits de logs ici]
```

---

## 💻 Environnement
- **OS** : [ex: Ubuntu 22.04, macOS Ventura, Windows 11]
- **Python** : [ex: 3.10.12]
- **Node.js** : [ex: 18.16.0]
- **Version d'Agent World** : [ex: v0.2.0]
- **Base de Données** : [ex: PostgreSQL 14, MongoDB 6.0]
- **Modèle IA** : [ex: Mistral, OpenAI]

---

## 🔗 Issues Liées
- Issue liée : #XXX
- Pull Request liée : #XXX

---

## 📌 Notes Supplémentaires
Toute information supplémentaire qui pourrait aider à résoudre le bug.
```

---

---

## 💡 **Template de Fonctionnalité**

**Titre** : `[FEAT] [Épic] Description de la fonctionnalité`
**Exemple** : `[FEAT] [VS Code] Ajouter un thème sombre automatique`

**Labels** : `enhancement`, `priority: high/medium/low`, `epic: [nom]`

**Corps** :
```markdown
## 💡 Description de la Fonctionnalité
Une description **détaillée** de la fonctionnalité proposée.

---

## 🎯 Problème Résolu
Quel **problème** cette fonctionnalité résout-elle ?

---

## ✅ Solution Proposée
Comment **implémenter** cette fonctionnalité ?

---

## 📌 Exemples
- **Exemple 1** : ...
- **Exemple 2** : ...

---

## 🔗 Ressources
- [Lien vers une documentation](url)
- [Exemple similaire dans un autre projet](url)

---

## 📅 Priorité
- [ ] **P0 (Must Have)** : Essentiel pour le MVP ou la prochaine version.
- [ ] **P1 (Should Have)** : Important mais pas critique.
- [x] **P2 (Could Have)** : Nice to have.

---

## 👥 Assigné à
@utilisateur (si applicable)

---

## 📝 User Story Associée
- **ID** : US-XXX
- **Lien** : [BACKLOG.md#us-xxx](BACKLOG.md#us-xxx)
```

---

---

## ❓ **Template de Question**

**Titre** : `[QUESTION] [Catégorie] Description de la question`
**Exemple** : `[QUESTION] [Installation] Comment configurer PostgreSQL ?`

**Labels** : `question`, `category: [installation/usage/development]`

**Corps** :
```markdown
## ❓ Question
Ma question est : **...**

---

## 🔍 Contexte
- Ce que j'ai **déjà essayé** : ...
- Les **erreurs** rencontrées : ...

---

## 💻 Environnement
- **OS** : [ex: Ubuntu 22.04]
- **Version d'Agent World** : [ex: v0.2.0]
- **Autres informations** : ...

---

## 📌 Notes Supplémentaires
Toute information supplémentaire qui pourrait aider à répondre à la question.
```

---

---

## 📜 **Template de Documentation**

**Titre** : `[DOCS] [Section] Mise à jour de la documentation`
**Exemple** : `[DOCS] [API] Ajouter la documentation pour l'endpoint /agents`

**Labels** : `documentation`, `priority: low`

**Corps** :
```markdown
## 📜 Section à Mettre à Jour
- [ ] README.md
- [ ] INSTALL.md
- [ ] BACKLOG.md
- [ ] ROADMAP.md
- [ ] CONTRIBUTING.md
- [ ] Autre : ...

---

## 📌 Description des Changements
Décrivez les **modifications** à apporter à la documentation.

---

## 🔗 Ressources
- [Lien vers la section actuelle](url)
- [Exemple de documentation](url)

---

## 📅 Priorité
- [ ] **Haute** : Documentation manquante ou incorrecte.
- [x] **Moyenne** : Amélioration de la documentation existante.
- [ ] **Basse** : Ajout de détails mineurs.
```

---

---

## 🔧 **Template de Tâche Technique**

**Titre** : `[TECH] [Composant] Description de la tâche`
**Exemple** : `[TECH] [Backend] Optimiser les requêtes SQL`

**Labels** : `technical-debt`, `priority: high/medium/low`, `component: [nom]`

**Corps** :
```markdown
## 🔧 Description de la Tâche
Une description **claire** de la tâche technique à réaliser.

---

## 🎯 Objectif
Quel est le **but** de cette tâche ?

---

## ✅ Critères d'Acceptation
- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

---

## 🔗 Tâches Liées
- Issue liée : #XXX
- Pull Request liée : #XXX

---

## 📅 Priorité
- [ ] **P0 (Must Have)** : Critique pour la stabilité ou la performance.
- [x] **P1 (Should Have)** : Important mais pas urgent.
- [ ] **P2 (Could Have)** : Amélioration mineure.
```

---

---

## 🎨 **Template de Design**

**Titre** : `[DESIGN] [Composant] Proposition de design`
**Exemple** : `[DESIGN] [UI] Nouveau design pour le dashboard`

**Labels** : `design`, `priority: medium/low`, `component: [ui/ux]`

**Corps** :
```markdown
## 🎨 Description du Design
Une description **détaillée** de la proposition de design.

---

## 📌 Problème Actuel
Quel est le **problème** avec le design actuel ?

---

## ✅ Solution Proposée
Décrivez votre **proposition** (avec maquettes ou captures d'écran si possible).

---

## 🖼️ Maquettes / Captures d'Écran
```
[Ajoutez des images ou des liens vers des maquettes (Figma, etc.)]
```

---

## 🔗 Ressources
- [Lien vers Figma](url)
- [Inspiration](url)

---

## 📅 Priorité
- [ ] **Haute** : Impact majeur sur l'UX.
- [x] **Moyenne** : Amélioration significative.
- [ ] **Basse** : Amélioration mineure.
```

---

---

## 📊 **Liste des Labels GitHub**

### **🔹 Par Type**
| **Label**               | **Description**                                                                                     | **Couleur**       |
|-------------------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `bug`                   | Bug à corriger.                                                                                   | `d73a4a` (rouge)   |
| `enhancement`           | Nouvelle fonctionnalité.                                                                         | `0075ca` (bleu)    |
| `question`              | Question ou demande de clarification.                                                             | `cc317c` (rose)    |
| `documentation`         | Mise à jour de la documentation.                                                                   | `0075ca` (bleu)    |
| `technical-debt`        | Tâche technique (refactorisation, optimisation, etc.).                                          | `f9c514` (jaune)   |
| `design`                | Proposition ou tâche liée au design.                                                              | `a4a9ad` (gris)    |

### **🔹 Par Priorité**
| **Label**               | **Description**                                                                                     | **Couleur**       |
|-------------------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `priority: high`        | Priorité élevée (P0).                                                                             | `d73a4a` (rouge)   |
| `priority: medium`      | Priorité moyenne (P1).                                                                             | `f9c514` (jaune)   |
| `priority: low`         | Priorité basse (P2).                                                                               | `0e8a16` (vert)    |

### **🔹 Par Épic**
| **Label**               | **Description**                                                                                     | **Couleur**       |
|-------------------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `epic: mvp`             | Épic 1 : MVP.                                                                                       | `0075ca` (bleu)    |
| `epic: vs-code`         | Épic 2 : Intégration VS Code.                                                                    | `0075ca` (bleu)    |
| `epic: files`           | Épic 3 : Gestion des Fichiers.                                                                   | `0075ca` (bleu)    |
| `epic: history`         | Épic 4 : Historique et Versioning.                                                              | `0075ca` (bleu)    |
| `epic: templates`       | Épic 5 : Templates et Personnalisation.                                                         | `0075ca` (bleu)    |
| `epic: collaboration`   | Épic 6 : Collaboration.                                                                           | `0075ca` (bleu)    |
| `epic: integrations`    | Épic 7 : Intégrations Externes.                                                                 | `0075ca` (bleu)    |
| `epic: performance`     | Épic 8 : Performance et Scalabilité.                                                            | `0075ca` (bleu)    |
| `epic: ux`             | Épic 9 : Expérience Utilisateur.                                                                | `0075ca` (bleu)    |
| `epic: security`        | Épic 10 : Sécurité et Conformité.                                                               | `0075ca` (bleu)    |

### **🔹 Par Composant**
| **Label**               | **Description**                                                                                     | **Couleur**       |
|-------------------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `component: backend`    | Backend (Flask/FastAPI).                                                                         | `0075ca` (bleu)    |
| `component: frontend`   | Frontend (React/Next.js).                                                                        | `0075ca` (bleu)    |
| `component: api`        | API REST/GraphQL.                                                                                 | `0075ca` (bleu)    |
| `component: cli`        | Interface en ligne de commande.                                                                   | `0075ca` (bleu)    |
| `component: vs-code`    | Extension VS Code.                                                                               | `0075ca` (bleu)    |
| `component: database`   | Base de données (PostgreSQL, MongoDB).                                                          | `0075ca` (bleu)    |
| `component: models`     | Modèles IA (Mistral, OpenAI, etc.).                                                              | `0075ca` (bleu)    |

### **🔹 Par Statut**
| **Label**               | **Description**                                                                                     | **Couleur**       |
|-------------------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `status: to do`         | À faire.                                                                                           | `fbca04` (orange)  |
| `status: in progress`   | En cours.                                                                                         | `0075ca` (bleu)    |
| `status: review`        | En revue.                                                                                          | `f9c514` (jaune)   |
| `status: done`          | Terminé.                                                                                          | `0e8a16` (vert)    |
| `status: blocked`       | Bloqué.                                                                                           | `d73a4a` (rouge)   |

---

## 📌 **Bonnes Pratiques pour les Issues**

### **✅ À Faire**
- **Utilisez un template** adapté au type d'issue.
- **Soyez clair et concis** dans la description.
- **Ajoutez des labels** pour faciliter le tri.
- **Liez les issues** entre elles (ex: `Closes #XXX`).
- **Ajoutez des captures d'écran ou des logs** si applicable.
- **Mentionnez les user stories** associées (ex: `US-011`).

### **❌ À Éviter**
- **Issues trop vagues** (ex: "Ça ne marche pas").
- **Issues dupliquées** (vérifiez d'abord les issues existantes).
- **Issues hors sujet** (utilisez les discussions pour les questions générales).
- **Issues sans labels** (ajoutez au moins un label).

---

## 🔗 **Ressources**

- [Backlog](https://github.com/GoupilJeremy/agent-world/blob/main/BACKLOG.md) : Détail des user stories.
- [Roadmap](https://github.com/GoupilJeremy/agent-world/blob/main/ROADMAP.md) : Timeline et objectifs.
- [Contributing](https://github.com/GoupilJeremy/agent-world/blob/main/CONTRIBUTING.md) : Guide pour contribuer.
- [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues) : Liste des issues existantes.

---

*Document généré le 06 août 2026. Dernière mise à jour : [DATE]*
