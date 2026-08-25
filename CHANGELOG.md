# 📜 **Agent World - Changelog**
*Historique des versions et changements*

---

## 📌 **Format**
Ce changelog suit les conventions de [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

### **Types de changements**
- `Added` : Nouveautés
- `Changed` : Modifications
- `Fixed` : Corrections de bugs
- `Removed` : Suppressions
- `Security` : Corrections de sécurité
- `Deprecated` : Fonctionnalités obsolètes

---

## 🚀 **Versions**

---

### **🔜 [Unreleased]**
*Changements en cours pour la prochaine version*

#### **Added**
- Ajout de la structure complète du backlog (60+ user stories, 10 épics).
- Création des fichiers de documentation (BACKLOG.md, ROADMAP.md, etc.).
- Configuration GitHub (labels, milestones, projects).
- Extension VS Code avec Activity Bar, liste des agents, dashboard et navigation
  vers leur détail (US-011).
- Adaptation automatique des vues aux couleurs du thème VS Code (US-012).
- Ouverture d’un fichier généré via le sélecteur et les URI natives de VS Code
  (US-013).
- Allowlist de commandes VS Code pour formater, organiser les imports et
  enregistrer les fichiers (US-014).
- Exécution d’agents depuis VS Code avec notifications de fin dédupliquées et
  accès direct au détail de l’agent (US-015).
- Adaptateur de débogage Agent World avec points d’arrêt sur le cycle
  d’exécution, pas à pas et inspection sécurisée des variables (US-016).
- Intégration à l’API Git native de VS Code : association agent/dépôt, détection
  des changements, sélection explicite des fichiers, suggestion de commit et
  push avec contrôle de l’amont (US-017).
- Finalisation synchrone des exécutions lancées par `POST /api/agents/{id}/run`,
  avec résultat et durée retournés à l’extension.
- Choix et persistance du dossier de sortie depuis le CLI, avec override ponctuel
  pour une exécution (US-018).
- Validation des dossiers et confinement des fichiers générés, avec écriture JSON
  atomique.
- Tests unitaires du gestionnaire de sortie et de son intégration CLI.
- Tests Node sans dépendances pour le manifeste, l’API, les vues et les commandes.

#### **Changed**
- Mise à jour de la structure du repository.
- Exécution des tests de l’extension dans les workflows CI et pull request.
- Correction du point d’entrée CLI et initialisation paresseuse de Flask pour que
  les commandes de configuration restent utilisables sans base de données active.

---

### **✅ [v0.1.0] - 06 août 2026**
*Minimum Viable Product (MVP)*

#### **Added**
- **Structure de Base** :
  - Initialisation du repository GitHub (US-001).
  - Architecture technique (backend, frontend, base de données) (US-002).
  - Modèles de données pour les agents, workflows et utilisateurs (US-003).
- **API** :
  - API REST/GraphQL pour gérer les agents (CRUD) (US-004).
  - Tests unitaires et E2E (US-007).
- **CLI** :
  - Interface en ligne de commande (create, list, delete) (US-005).
  - Documentation CLI.
- **Intégration IA** :
  - Support pour 2+ modèles d'IA (Mistral, OpenAI) (US-006).
  - Configuration des clés API.
- **Documentation** :
  - README.md avec guide d'installation et exemples (US-008).
  - Guide de contribution (CONTRIBUTING.md).
- **Déploiement** :
  - Déploiement initial sur un serveur de test (US-009).
  - URL accessible pour les utilisateurs testeurs.

#### **Changed**
- Première version stable du MVP.

#### **Fixed**
- Corrections initiales des bugs identifiés pendant les tests.

---

### **📅 [v0.0.1] - 01 juillet 2026**
*Version initiale (Pre-Alpha)*

#### **Added**
- Création du repository GitHub.
- Structure de base du projet.
- Configuration initiale de la CI/CD (GitHub Actions).

---

## 🗓️ **Calendrier des Versions**

| **Version** | **Date**       | **Nom**               | **Épics**                          | **Statut**          |
|-------------|----------------|------------------------|------------------------------------|---------------------|
| v0.0.1      | 01 juillet 2026| Pre-Alpha             | -                                  | ✅ **Terminé**       |
| v0.1.0      | 06 août 2026   | MVP                    | Épic 1                              | ✅ **Terminé**       |
| v0.2.0      | 12 août 2026   | VS Code + Files       | Épic 2, Épic 3                     | ⏳ **En cours**      |
| v0.2.1      | 19 août 2026   | Files Advanced        | Épic 3                              | ⏳ **À venir**       |
| v0.3.0      | 30 septembre 2026| History + Templates   | Épic 4, Épic 5                     | ⏳ **À venir**       |
| v0.4.0      | 30 octobre 2026| Collaboration         | Épic 6                              | ⏳ **À venir**       |
| v0.5.0      | 30 novembre 2026| Integrations         | Épic 7                              | ⏳ **À venir**       |
| v0.6.0      | 20 décembre 2026| Performance           | Épic 8                              | ⏳ **À venir**       |
| v0.7.0      | 30 janvier 2027 | UX + Security         | Épic 9, Épic 10                    | ⏳ **À venir**       |
| v0.8.0      | 28 février 2027 | Multi-Modèles         | -                                  | ⏳ **À venir**       |
| v0.9.0      | 31 mars 2027   | Entreprise            | -                                  | ⏳ **À venir**       |
| v1.0.0      | 30 avril 2027  | Version Stable        | -                                  | ⏳ **À venir**       |

---

## 📊 **Statistiques**

### **📈 Versions par Trimestre**
- **Q3 2026** : 3 versions (v0.0.1, v0.1.0, v0.2.0, v0.2.1)
- **Q4 2026** : 3 versions (v0.3.0, v0.4.0, v0.5.0, v0.6.0)
- **Q1 2027** : 3 versions (v0.7.0, v0.8.0, v0.9.0)
- **Q2 2027** : 1 version (v1.0.0)

### **⏱️ Fréquence des Versions**
- **Phase MVP** : 1 version toutes les 1-2 semaines.
- **Phase Bêta** : 1 version par mois.
- **Phase Stable** : 1 version majeure tous les 3-6 mois.

---

## 🔗 **Liens Utiles**
- [Backlog](BACKLOG.md) : Détail des fonctionnalités à venir.
- [Roadmap](ROADMAP.md) : Timeline et objectifs.
- [Repository GitHub](https://github.com/GoupilJeremy/agent-world)
- [Documentation](README.md)

---

## 📝 **Comment Contribuer**
1. Consultez les [issues ouvertes](https://github.com/GoupilJeremy/agent-world/issues).
2. Lisez le [guide de contribution](CONTRIBUTING.md).
3. Créez une **branche** pour votre fonctionnalité (`git checkout -b feature/US-XXX`).
4. Commitez vos changements (`git commit -m "feat: ajouter [fonctionnalité] (US-XXX)"`).
5. Poussez vers la branche (`git push origin feature/US-XXX`).
6. Ouvrez une **Pull Request** vers `main`.

---

*Document généré le 06 août 2026. Dernière mise à jour : 25 août 2026.*
