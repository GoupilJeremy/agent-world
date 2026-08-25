# 🌍 **Agent World**
*La plateforme open-source pour créer, gérer et déployer des agents IA.*

---

## 📌 **Table des Matières**
1. [🎯 À Propos](#-à-propos)
2. [🚀 Fonctionnalités](#-fonctionnalités)
3. [📦 Installation](#-installation)
4. [🛠️ Utilisation](#-utilisation)
5. [🏗️ Architecture](#-architecture)
6. [🤝 Contribution](#-contribution)
7. [📜 Licence](#-licence)
8. [🔗 Ressources](#-ressources)

---

## 🎯 **À Propos**

**Agent World** est une plateforme **open-source** conçue pour simplifier la création, la gestion et le déploiement d'**agents IA**. Que vous soyez un développeur, un data scientist ou une équipe DevOps, Agent World vous permet de :

- ✅ **Créer des agents IA** sans expertise technique approfondie.
- ✅ **Gérer des workflows complexes** avec une interface intuitive.
- ✅ **Collaborer en équipe** sur des projets d'IA.
- ✅ **Intégrer avec des outils externes** (VS Code, GitHub, Slack, etc.).

### **🌟 Pourquoi Agent World ?**
- **Open Source** : 100% transparent et contribuable par la communauté.
- **Modulaire** : Architecture plug-and-play pour une extensibilité maximale.
- **Collaboratif** : Outils intégrés pour le travail d'équipe.
- **Performant** : Optimisé pour des workflows rapides et scalables.
- **Sécurisé** : Conforme aux standards les plus stricts (RGPD, SOC 2).

---

## 🚀 **Fonctionnalités**

### **🔹 Fonctionnalités de Base (MVP - v0.1.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Gestion des Agents**          | Créer, modifier, supprimer et lister des agents IA.                                               | ✅ **Disponible**    | v0.1.0      |
| **API REST/GraphQL**             | API pour interagir avec les agents (CRUD).                                                        | ✅ **Disponible**    | v0.1.0      |
| **Interface CLI**                | Commandes en ligne de commande pour gérer les agents.                                            | ✅ **Disponible**    | v0.1.0      |
| **Intégration Modèles IA**       | Support pour Mistral, OpenAI, et autres modèles.                                                  | ✅ **Disponible**    | v0.1.0      |
| **Tests Automatisés**            | Tests unitaires et E2E pour garantir la qualité.                                                   | ✅ **Disponible**    | v0.1.0      |

### **🔹 Intégration VS Code (v0.2.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Dashboard VS Code**           | Visualiser les agents et ouvrir leur détail directement depuis VS Code.                           | ✅ **Disponible**    | v0.2.0      |
| **Thème Automatique**           | Adaptation automatique au thème VS Code (clair/sombre et contraste élevé).                       | ✅ **Disponible**    | v0.2.0      |
| **Ouverture de Fichiers**       | Choisir et ouvrir un fichier généré avec le sélecteur natif de VS Code.                           | ✅ **Disponible**    | v0.2.0      |
| **Exécution de Commandes**      | Exécuter des commandes VS Code depuis Agent World.                                               | ⏳ **À venir**       | v0.2.0      |
| **Notifications**               | Recevoir des notifications dans VS Code.                                                         | ⏳ **À venir**       | v0.2.1      |

### **🔹 Gestion des Fichiers (v0.2.0 - v0.2.1)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Dossier de Sortie Personnalisé** | Choisir et mémoriser un dossier de sortie validé depuis le CLI.                                 | ✅ **Disponible**    | v0.2.0      |
| **Noms de Fichiers Intelligents** | Générer des noms de fichiers basés sur le contenu.                                               | ⏳ **En cours**      | v0.2.0      |
| **Organisation en Dossiers**    | Structure de dossiers automatique (ex: `/agents/{name}/outputs/`).                              | ⏳ **À venir**       | v0.2.1      |
| **Versioning des Fichiers**     | Versionner les fichiers générés (ex: `v1`, `v2`).                                                | ⏳ **À venir**       | v0.2.1      |
| **Nettoyage Automatique**       | Supprimer les fichiers temporaires ou obsolètes.                                                 | ⏳ **À venir**       | v0.3.0      |

### **🔹 Historique et Versioning (v0.3.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Historique des Agents**       | Stocker l'historique des modifications des agents.                                               | ⏳ **À venir**       | v0.3.0      |
| **Historique des Exécutions**   | Enregistrer les exécutions des agents (date, durée, résultat).                                   | ⏳ **À venir**       | v0.3.0      |
| **Restauration de Versions**    | Restaurer une version précédente d'un agent.                                                     | ⏳ **À venir**       | v0.3.0      |
| **Comparaison de Versions**     | Comparer deux versions d'un agent (diff visuel).                                                 | ⏳ **À venir**       | v0.3.0      |

### **🔹 Templates et Personnalisation (v0.3.0 - v0.3.1)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Création de Templates**       | Créer des templates d'agents réutilisables.                                                        | ⏳ **À venir**       | v0.3.0      |
| **Bibliothèque de Templates**    | Bibliothèque de templates partagés par la communauté.                                            | ⏳ **À venir**       | v0.3.0      |
| **Import/Export de Templates**   | Importer et exporter des templates (JSON/YAML).                                                   | ⏳ **À venir**       | v0.3.1      |
| **Personnalisation**            | Personnaliser un template avant utilisation.                                                      | ⏳ **À venir**       | v0.3.1      |

### **🔹 Collaboration (v0.4.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Invitation d'Utilisateurs**   | Inviter des utilisateurs à rejoindre un projet.                                                   | ⏳ **À venir**       | v0.4.0      |
| **Gestion des Rôles**           | Définir des rôles avec des permissions spécifiques.                                              | ⏳ **À venir**       | v0.4.0      |
| **Partage de Projets**          | Partager un projet avec une équipe ou un utilisateur.                                             | ⏳ **À venir**       | v0.4.0      |
| **Commentaires**                 | Ajouter des commentaires sur les agents.                                                          | ⏳ **À venir**       | v0.4.0      |
| **Chat en Temps Réel**          | Chat intégré pour discuter avec l'équipe.                                                         | ⏳ **À venir**       | v0.4.0      |

### **🔹 Intégrations Externes (v0.5.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **GitHub**                      | Connecter Agent World à GitHub (PR, issues, etc.).                                                | ⏳ **À venir**       | v0.5.0      |
| **Slack**                       | Envoyer des notifications et interagir avec Slack.                                               | ⏳ **À venir**       | v0.5.0      |
| **Discord**                     | Envoyer des notifications et interagir avec Discord.                                             | ⏳ **À venir**       | v0.5.0      |
| **Notion**                      | Synchroniser les agents avec des bases de données Notion.                                        | ⏳ **À venir**       | v0.5.0      |
| **Google Drive**                | Stocker et récupérer des fichiers depuis Google Drive.                                           | ⏳ **À venir**       | v0.5.0      |
| **Trello**                      | Créer des cartes Trello à partir des tâches des agents.                                          | ⏳ **À venir**       | v0.5.0      |

### **🔹 Performance et Scalabilité (v0.6.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Optimisation API**            | Réduire la latence des requêtes API (caching, pagination).                                        | ⏳ **À venir**       | v0.6.0      |
| **Mise en Cache**               | Mettre en cache les résultats des agents.                                                         | ⏳ **À venir**       | v0.6.0      |
| **Scalabilité Horizontale**     | Permettre le scaling horizontal (Kubernetes).                                                   | ⏳ **À venir**       | v0.6.0      |
| **Monitoring**                  | Ajouter un système de monitoring (Prometheus, Grafana).                                           | ⏳ **À venir**       | v0.6.0      |

### **🔹 Expérience Utilisateur (v0.7.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Design System**               | Design system cohérent pour l'UI.                                                                 | ⏳ **À venir**       | v0.7.0      |
| **Accessibilité**               | Rendre l'application accessible (WCAG 2.1 AA).                                                   | ⏳ **À venir**       | v0.7.0      |
| **Internationalisation**         | Traduire l'application en français et anglais.                                                  | ⏳ **À venir**       | v0.7.0      |
| **Thème Personnalisable**       | Permettre aux utilisateurs de personnaliser le thème.                                           | ⏳ **À venir**       | v0.7.0      |

### **🔹 Sécurité et Conformité (v0.7.0 - v0.9.0)**
| **Fonctionnalité**               | **Description**                                                                                     | **Statut**          | **Version** |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-------------|
| **Authentification 2FA**        | Ajouter une authentification à 2 facteurs.                                                        | ⏳ **À venir**       | v0.7.0      |
| **Gestion des Permissions**     | Définir des permissions fines pour les utilisateurs.                                            | ⏳ **À venir**       | v0.7.0      |
| **Chiffrement des Données**     | Chiffrer les données sensibles (clés API, messages privés).                                      | ⏳ **À venir**       | v0.8.0      |
| **Audit des Logs**              | Enregistrer et auditer les actions des utilisateurs.                                            | ⏳ **À venir**       | v0.8.0      |
| **Conformité RGPD**             | Rendre la plateforme conforme au RGPD.                                                           | ⏳ **À venir**       | v0.9.0      |
| **Conformité SOC 2**            | Conformité aux standards SOC 2 pour les entreprises.                                            | ⏳ **À venir**       | v0.9.0      |

---

## 📦 **Installation**

### **🔹 Prérequis**
- **Système d'exploitation** : Linux, macOS, ou Windows (WSL recommandé pour Windows).
- **Python** : 3.10 ou supérieur.
- **Node.js** : 18.x ou supérieur (pour le frontend).
- **Git** : 2.x ou supérieur.
- **Docker** : 20.x ou supérieur (optionnel, pour le déploiement).
- **Base de données** : PostgreSQL 14+ ou MongoDB 6+.

### **🔹 Installation Rapide**

#### **1. Cloner le Repository**
```bash
git clone https://github.com/GoupilJeremy/agent-world.git
cd agent-world
```

#### **2. Configurer l'Environnement**
```bash
# Créer un environnement virtuel (Python)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate   # Windows

# Installer les dépendances backend
pip install -r requirements.txt

# Installer les dépendances frontend (si applicable)
cd frontend
npm install
cd ..
```

#### **3. Configurer les Variables d'Environnement**
Créez un fichier `.env` à la racine du projet avec les variables suivantes :
```env
# Backend
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=votre_clé_secrète
DATABASE_URL=postgresql://user:password@localhost:5432/agent_world

# Modèles IA (exemple pour Mistral)
MISTRAL_API_KEY=votre_clé_api_mistral
OPENAI_API_KEY=votre_clé_api_openai

# Frontend (si applicable)
REACT_APP_API_URL=http://localhost:5000
```

#### **4. Initialiser la Base de Données**
```bash
# Pour PostgreSQL
flask db init
flask db migrate
flask db upgrade

# Pour MongoDB
python scripts/init_mongo.py
```

#### **5. Démarrer l'Application**
```bash
# Démarrer le backend
flask run

# Démarrer le frontend (dans un autre terminal)
cd frontend
npm start
```

#### **6. Accéder à l'Application**
- **Backend** : [http://localhost:5000](http://localhost:5000)
- **Frontend** : [http://localhost:3000](http://localhost:3000)

---

### **🔹 Installation avec Docker**

#### **1. Construire les Images**
```bash
docker-compose build
```

#### **2. Démarrer les Conteneurs**
```bash
docker-compose up -d
```

#### **3. Accéder à l'Application**
- **Backend** : [http://localhost:5000](http://localhost:5000)
- **Frontend** : [http://localhost:3000](http://localhost:3000)
- **Base de données** : Accès via `localhost:5432` (PostgreSQL) ou `localhost:27017` (MongoDB).

---

## 🛠️ **Utilisation**

### **🔹 Interface CLI**

#### **Commandes de Base**
| **Commande**               | **Description**                                                                                     | **Exemple**                          |
|----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `agent create`             | Créer un nouvel agent.                                                                              | `agent create --name my_agent`       |
| `agent list`               | Lister tous les agents.                                                                             | `agent list`                         |
| `agent show <id>`          | Afficher les détails d'un agent.                                                                  | `agent show 123`                     |
| `agent update <id>`        | Mettre à jour un agent.                                                                            | `agent update 123 --name new_name`   |
| `agent delete <id>`        | Supprimer un agent.                                                                                | `agent delete 123`                   |
| `agent run <id>`           | Exécuter un agent.                                                                                  | `agent run 123 --input "Hello!"`     |
| `agent config output-dir`  | Afficher, choisir ou réinitialiser le dossier de sortie.                                          | `agent config output-dir ./results`  |

#### **Options Avancées**
| **Option**                 | **Description**                                                                                     | **Exemple**                          |
|----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `--model`                  | Spécifier le modèle IA à utiliser.                                                                | `agent run 123 --model mistral`      |
| `--output`                 | Spécifier un nom de fichier relatif au dossier de sortie.                                         | `agent run 123 --input "Hello!" --output result.json` |
| `--output-dir`             | Remplacer le dossier configuré pour une seule exécution.                                          | `agent run 123 --input "Hello!" --output result.json --output-dir ./tmp` |
| `--verbose`                | Afficher les logs détaillés.                                                                      | `agent run 123 --verbose`            |

Le dossier persistant se configure avec `agent config output-dir <dossier>`, se
consulte sans argument et se réinitialise avec
`agent config output-dir --reset`. Le chemin est créé si nécessaire, vérifié en
écriture et mémorisé dans la configuration utilisateur du système. La variable
`AGENT_WORLD_CONFIG_FILE` permet de déplacer ce fichier de préférences.

Pour une exécution, l’ordre de priorité est `--output-dir`, le choix persistant,
la variable `OUTPUT_DIR`, puis le dossier `outputs`. Les chemins absolus et les
traversées avec `..` sont refusés ; l’écriture JSON est atomique.

---

### **🔹 API REST**

#### **Endpoints Principaux**
| **Méthode** | **Endpoint**               | **Description**                                                                                     | **Exemple**                          |
|-------------|----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `GET`       | `/api/agents`              | Lister tous les agents.                                                                             | `curl http://localhost:5000/api/agents` |
| `POST`      | `/api/agents`              | Créer un nouvel agent.                                                                              | `curl -X POST -H "Content-Type: application/json" -d '{"name": "my_agent"}' http://localhost:5000/api/agents` |
| `GET`       | `/api/agents/<id>`        | Récupérer un agent spécifique.                                                                     | `curl http://localhost:5000/api/agents/123` |
| `PUT`       | `/api/agents/<id>`        | Mettre à jour un agent.                                                                            | `curl -X PUT -H "Content-Type: application/json" -d '{"name": "new_name"}' http://localhost:5000/api/agents/123` |
| `DELETE`    | `/api/agents/<id>`        | Supprimer un agent.                                                                                | `curl -X DELETE http://localhost:5000/api/agents/123` |
| `POST`      | `/api/agents/<id>/run`    | Exécuter un agent.                                                                                  | `curl -X POST -H "Content-Type: application/json" -d '{"input": "Hello!"}' http://localhost:5000/api/agents/123/run` |

#### **Exemple de Réponse (GET /api/agents)**
```json
{
  "agents": [
    {
      "id": 123,
      "name": "my_agent",
      "model": "mistral",
      "created_at": "2026-08-06T10:00:00Z",
      "updated_at": "2026-08-06T10:00:00Z"
    }
  ]
}
```

---

### **🔹 Intégration VS Code**

L’extension est actuellement disponible depuis les sources du dépôt. Consultez
son [guide dédié](vscode-extension/README.md) pour le développement et les tests.

#### **1. Lancer l'Extension en Développement**
1. Démarrez le backend avec `python run.py` depuis la racine du dépôt.
2. Ouvrez le dossier `vscode-extension/` dans VS Code.
3. Appuyez sur **F5** et lancez un **Extension Development Host**.

#### **2. Configurer l'Extension**
1. Ouvrez les paramètres de l'extension (Ctrl+,).
2. Configurez l'URL de l'API Agent World :
   ```json
   {
     "agentWorld.apiUrl": "http://127.0.0.1:5000"
   }
   ```

#### **3. Utiliser l'Extension**
- **Afficher les agents** : ouvrez l'icône Agent World dans l’Activity Bar.
- **Ouvrir le Dashboard** : utilisez l’action Dashboard dans l’en-tête de la vue.
- **Voir un détail** : cliquez sur un agent dans l’arborescence.
- **Ouvrir un fichier** : lancez `Agent World: Ouvrir un fichier généré`.

---

## 🏗️ **Architecture**

### **🔹 Schéma Global**
```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                AGENT WORLD                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────────┐  │
│  │   Frontend   │    │    Backend   │    │             Base de Données           │  │
│  │ (React/Next) │◄──►│ (Flask/FastAPI)│◄──►│  PostgreSQL / MongoDB / Redis (Cache)  │  │
│  └─────────────┘    └─────────────┘    └─────────────────────────────────────┘  │
│           ▲                  ▲  ▲  ▲                                              │
│           │                  │  │  └──────────────────────────────────────────────┘  │
│           │                  │  │                                                   │
│           │                  │  └──► Modèles IA (Mistral, OpenAI, Anthropic, etc.)    │
│           │                  │                                                   │
│           │                  └──► Intégrations (GitHub, Slack, Discord, etc.)       │
│           │                                                                       │
│           └───────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                        Interface CLI (Python)                            │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### **🔹 Composants Principaux**

#### **1. Frontend**
- **Technologies** : React.js / Next.js, TypeScript, Tailwind CSS.
- **Fonctionnalités** :
  - Dashboard pour gérer les agents.
  - Éditeur de templates.
  - Visualisation des résultats.
  - Intégration avec VS Code.

#### **2. Backend**
- **Technologies** : Flask / FastAPI (Python), SQLAlchemy / MongoEngine.
- **Fonctionnalités** :
  - API REST/GraphQL pour gérer les agents.
  - Intégration avec les modèles IA.
  - Gestion des utilisateurs et des permissions.
  - Cache (Redis) pour les résultats.

#### **3. Base de Données**
- **Options** : PostgreSQL (recommandé), MongoDB, SQLite (pour le développement).
- **Schéma** :
  - `agents` : Table des agents.
  - `users` : Table des utilisateurs.
  - `workflows` : Table des workflows.
  - `executions` : Table des exécutions.
  - `templates` : Table des templates.

#### **4. Modèles IA**
- **Support** : Mistral, OpenAI, Anthropic, Llama, Gemma, etc.
- **Intégration** : Via des connecteurs dédiés (ex: `MistralConnector`, `OpenAIConnector`).

#### **5. Intégrations Externes**
- **GitHub** : Gestion des repositories, PR, issues.
- **Slack/Discord** : Notifications et commandes.
- **Notion/Google Drive** : Stockage et synchronisation.
- **VS Code** : Extension dédiée.

---

## 🤝 **Contribution**

### **🔹 Comment Contribuer ?**
1. **Lire la Documentation** :
   - [Backlog](BACKLOG.md) : Détail des fonctionnalités à implémenter.
   - [Roadmap](ROADMAP.md) : Timeline et objectifs.
   - [Contributing](CONTRIBUTING.md) : Guide complet pour contribuer.

2. **Trouver une Issue** :
   - Consultez les [issues ouvertes](https://github.com/GoupilJeremy/agent-world/issues).
   - Filtrez par **label** (ex: `good first issue`, `help wanted`).

3. **Créer une Branche** :
   ```bash
   git checkout -b feature/US-XXX
   ```

4. **Implémenter la Fonctionnalité** :
   - Suivez les **critères d'acceptation** de la user story.
   - Respectez les **conventions de code** (voir [CONTRIBUTING.md](CONTRIBUTING.md)).

5. **Tester** :
   - Écrivez des **tests unitaires** et **E2E**.
   - Vérifiez que tous les tests passent :
     ```bash
     pytest
     ```

6. **Commiter** :
   ```bash
   git commit -m "feat: ajouter [fonctionnalité] (US-XXX)"
   ```

7. **Pousser et Ouvrir une PR** :
   ```bash
   git push origin feature/US-XXX
   ```
   - Ouvrez une **Pull Request** vers `main`.
   - Remplissez le template de PR (lien vers l'issue, description, etc.).

### **🔹 Règles de Contribution**
- **Respectez le [Code de Conduite](CODE_OF_CONDUCT.md)**.
- **Suivez les conventions de commit** :
  - `feat:` : Nouvelle fonctionnalité.
  - `fix:` : Correction de bug.
  - `docs:` : Mise à jour de la documentation.
  - `refactor:` : Refactorisation du code.
  - `chore:` : Tâches de maintenance.
- **Écrivez des tests** pour toute nouvelle fonctionnalité.
- **Documentez votre code** (commentaires, docstrings).

### **🔹 Rejoindre la Communauté**
- **Discord** : [Lien à ajouter](https://discord.gg/)
- **Discussions GitHub** : [Agent World Discussions](https://github.com/GoupilJeremy/agent-world/discussions)
- **Email** : goupiljeremy@gmail.com

---

## 📜 **Licence**

**Agent World** est distribué sous la licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

```
MIT License

Copyright (c) 2026 GoupilJeremy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🔗 **Ressources**

### **📚 Documentation**
- [Backlog](BACKLOG.md) : Détail des fonctionnalités.
- [Roadmap](ROADMAP.md) : Timeline et objectifs.
- [Changelog](CHANGELOG.md) : Historique des versions.
- [Contributing](CONTRIBUTING.md) : Guide pour contribuer.
- [Installation](INSTALL.md) : Instructions détaillées.
- [Code de Conduite](CODE_OF_CONDUCT.md) : Règles de la communauté.

### **🛠️ Outils**
- **Repository** : [GoupilJeremy/agent-world](https://github.com/GoupilJeremy/agent-world)
- **Issues** : [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues)
- **Pull Requests** : [GitHub PRs](https://github.com/GoupilJeremy/agent-world/pulls)
- **Actions** : [GitHub Actions](https://github.com/GoupilJeremy/agent-world/actions)

### **📢 Communication**
- **Email** : goupiljeremy@gmail.com
- **Twitter** : [@AgentWorld](https://twitter.com/AgentWorld)
- **Blog** : [agent-world.dev/blog](https://agent-world.dev/blog)

---

## 🙏 **Remerciements**

Un grand merci à :
- **La communauté open-source** pour ses contributions.
- **Mistral AI** pour son soutien et ses modèles d'IA.
- **Tous les contributeurs** qui aident à améliorer Agent World.

---

*Document généré le 06 août 2026. Dernière mise à jour : 25 août 2026.*
