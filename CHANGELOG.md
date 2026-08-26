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
- **Intégrations Externes (Épic 7 - Sprint 4)** :
  - Intégration Slack complète (US-048) :
    - Envoi de messages aux canaux et utilisateurs.
    - Gestion des canaux (liste, création, rejoindre, quitter).
    - Gestion des utilisateurs et réactions.
    - Support OAuth2 et Bot Token.
    - plus de 20 actions supportées.
  - Intégration Discord complète (US-049) :
    - Envoi de messages et embeds riches.
    - Gestion des salons (canaux) et serveurs (guildes).
    - Gestion des rôles et membres.
    - Support des commandes slash personnalisées.
    - Gestion des webhooks Discord.
    - plus de 34 actions supportées.
  - Webhooks personnalisés (US-053) :
    - Système de gestion des abonnements webhooks.
    - Distribution des événements aux handlers appropriés.
    - Validation des signatures de sécurité.
    - Support des webhooks entrants et sortants.
    - Statistiques et monitoring.
  - Tests complets pour toutes les intégrations.
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

### **✅ [v0.2.1] - 25 août 2026**
*Épic 3 : Gestion des Fichiers (Complète)*

#### **Added**
- **Gestion avancée des fichiers** :
  - Organisation automatique en dossiers (`/agents/{name}/outputs/`) (US-020).
  - Versioning des fichiers avec historique et restauration (US-021).
  - Nettoyage automatique des fichiers temporaires/obsolètes (US-022).
  - Partage de fichiers avec permissions (lecture/écriture) (US-023).
  - Prévisualisation des fichiers (Markdown, JSON, TXT) (US-024).

#### **Changed**
- Correction du test `test_cleanup_restores_staged_files_when_database_commit_fails`.

#### **Fixed**
- Amélioration de la robustesse du système de fichiers.

---

### **✅ [v0.2.0] - 12 août 2026**
*Épic 2 : Intégration VS Code + Épic 3 (partielle)*

#### **Added**
- **Extension VS Code** :
  - Dashboard pour visualiser les agents (US-011).
  - Thème automatique (clair/sombre) (US-012).
  - Ouverture des fichiers dans VS Code (US-013).
  - Exécution de commandes VS Code (US-014).
  - Notifications (US-015).
  - Debugging des agents (US-016).
  - Intégration Git (US-017).
- **Gestion des fichiers** :
  - Dossier de sortie personnalisé via CLI (US-018).
  - Noms de fichiers intelligents (US-019).

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
| v0.2.0      | 12 août 2026   | VS Code + Files       | Épic 2, Épic 3 (partielle)          | ✅ **Terminé**      |
| v0.2.1      | 25 août 2026   | Files Complete        | Épic 3 (complète)                  | ✅ **Terminé**       |
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

*Document généré le 06 août 2026. Dernière mise à jour : 26 août 2026.*
