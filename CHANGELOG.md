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

#### **Changed**
- Mise à jour de la structure du repository.

---

### **✅ [v0.2.0] - 12 août 2026**
*Intégration VS Code + Gestion des Fichiers*

#### **Added**
- **VS Code Integration** :
  - Extension VS Code pour interagir avec Agent World.
  - Dashboard pour visualiser les agents depuis VS Code (US-011).
  - Thème automatique adapté à VS Code (clair/sombre) (US-012).
  - Ouverture des fichiers générés directement dans VS Code (US-013).
  - Exécution de commandes VS Code depuis Agent World (US-014).
- **Gestion des Fichiers** :
  - Dossier de sortie personnalisé (US-018).
  - Noms de fichiers intelligents basés sur le contenu (US-019).
  - Organisation automatique en dossiers (US-020).

#### **Changed**
- Amélioration de l'API pour supporter les nouvelles fonctionnalités.
- Mise à jour de la documentation (README.md, INSTALL.md).

#### **Fixed**
- Corrections mineures de bugs dans l'API et le CLI.

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

*Document généré le 06 août 2026. Dernière mise à jour : [DATE]*
