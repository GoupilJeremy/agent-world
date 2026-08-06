# 🤝 **Agent World - Guide de Contribution**
*Comment contribuer au projet Agent World*

---

## 📌 **Table des Matières**
1. [🎯 Introduction](#-introduction)
2. [🚀 Prérequis](#-prérequis)
3. [📦 Installation](#-installation)
4. [🛠️ Workflow de Contribution](#-workflow-de-contribution)
5. [📝 Conventions de Code](#-conventions-de-code)
6. [🧪 Tests](#-tests)
7. [📜 Documentation](#-documentation)
8. [🐛 Signaler un Bug](#-signaler-un-bug)
9. [💡 Proposer une Fonctionnalité](#-proposer-une-fonctionnalité)
10. [🤝 Code de Conduite](#-code-de-conduite)
11. [📊 Bonnes Pratiques](#-bonnes-pratiques)
12. [🔗 Ressources](#-ressources)

---

## 🎯 **Introduction**

Merci de votre intérêt pour **Agent World** ! 🎉

Ce guide vous explique comment contribuer au projet, que vous soyez un **développeur**, un **designer**, un **testeur**, ou simplement un **utilisateur** souhaitant aider.

### **🌟 Pourquoi Contribuer ?**
- **Apprendre** : Améliorez vos compétences en développement, IA, et collaboration.
- **Impact** : Contribuez à un projet open-source utilisé par des milliers de personnes.
- **Réseautage** : Rejoignez une communauté de passionnés d'IA.
- **Reconnaissance** : Votre nom apparaîtra dans les [contributeurs](https://github.com/GoupilJeremy/agent-world/graphs/contributors).

### **📌 Types de Contributions**
| **Type**               | **Description**                                                                                     | **Exemples**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **Code**               | Développer de nouvelles fonctionnalités ou corriger des bugs.                                   | Pull Requests, Issues                |
| **Documentation**      | Améliorer ou traduire la documentation.                                                           | README.md, Guides, Tutoriels         |
| **Tests**              | Écrire des tests pour garantir la qualité du code.                                               | Tests unitaires, E2E                 |
| **Design**             | Améliorer l'interface utilisateur ou créer des maquettes.                                        | Figma, CSS, Composants React         |
| **Feedback**           | Donner votre avis sur les fonctionnalités existantes ou à venir.                                | Issues, Discussions GitHub          |
| **Évangelisation**     | Promouvoir Agent World (articles, talks, réseaux sociaux).                                      | Blogs, Conférences, Twitter          |

---

## 🚀 **Prérequis**

### **🔹 Compétences Recommandées**
- **Développement** : Python, JavaScript/TypeScript, React, Flask/FastAPI.
- **Base de Données** : PostgreSQL, MongoDB, Redis.
- **Outils** : Git, GitHub, Docker, CI/CD (GitHub Actions).
- **IA** : Connaissance des modèles de langage (LLM) et des APIs (Mistral, OpenAI).

### **🔹 Environnement de Développement**
Voir [INSTALL.md](INSTALL.md) pour les instructions détaillées.

---

## 📦 **Installation**

### **🔹 Cloner le Repository**
```bash
git clone https://github.com/GoupilJeremy/agent-world.git
cd agent-world
```

### **🔹 Configurer l'Environnement**
Suivez les instructions dans [INSTALL.md](INSTALL.md) pour :
1. Installer les dépendances (Python, Node.js, etc.).
2. Configurer les variables d'environnement (`.env`).
3. Initialiser la base de données.
4. Démarrer l'application.

### **🔹 Vérifier l'Installation**
```bash
# Démarrer le backend
flask run

# Démarrer le frontend (si applicable)
cd frontend
npm start
```
- **Backend** : [http://localhost:5000](http://localhost:5000)
- **Frontend** : [http://localhost:3000](http://localhost:3000)

---

## 🛠️ **Workflow de Contribution**

### **🔹 1. Trouver une Issue**
1. Allez sur [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues).
2. Filtrez par :
   - **Label** : `good first issue` (pour les débutants), `help wanted`, `bug`, `enhancement`.
   - **Milestone** : Sélectionnez un sprint ou une version.
   - **Épic** : Filtrez par épic (ex: `VS Code`, `Files`, `History`).

### **🔹 2. Commenter sur l'Issue**
- **Signalez votre intention** de travailler sur l'issue en commentant :
  ```
  Je m'occupe de cette issue ! 🚀
  ```
- **Attendez la confirmation** d'un maintainer (pour éviter les doublons).

### **🔹 3. Créer une Branche**
- **Nommez votre branche** selon la convention :
  - `feature/US-XXX` : Pour une nouvelle fonctionnalité (ex: `feature/US-011`).
  - `fix/US-XXX` : Pour une correction de bug (ex: `fix/US-004`).
  - `docs/US-XXX` : Pour une mise à jour de documentation (ex: `docs/README`).
  - `refactor/US-XXX` : Pour une refactorisation (ex: `refactor/api`).
  - `chore/US-XXX` : Pour une tâche de maintenance (ex: `chore/dependencies`).

```bash
git checkout -b feature/US-XXX
```

### **🔹 4. Implémenter la Fonctionnalité**
- **Suivez les critères d'acceptation** de la user story (voir [BACKLOG.md](BACKLOG.md)).
- **Respectez les conventions de code** (voir [Conventions de Code](#-conventions-de-code)).
- **Écrivez des tests** (voir [Tests](#-tests)).

### **🔹 5. Commiter vos Changements**
- **Messages de commit** : Suivez la convention [Conventional Commits](https://www.conventionalcommits.org/) :
  - `feat:` : Nouvelle fonctionnalité.
  - `fix:` : Correction de bug.
  - `docs:` : Mise à jour de la documentation.
  - `refactor:` : Refactorisation du code.
  - `chore:` : Tâches de maintenance.
  - `test:` : Ajout de tests.

```bash
# Exemple pour une nouvelle fonctionnalité
git commit -m "feat: ajouter dashboard VS Code (US-011)"

# Exemple pour une correction de bug
git commit -m "fix: corriger l'affichage des agents dans VS Code (US-011)"
```

- **Incluez le numéro de l'issue** dans le message de commit (ex: `US-011`).

### **🔹 6. Pousser vers votre Branche**
```bash
git push origin feature/US-XXX
```

### **🔹 7. Ouvrir une Pull Request (PR)**
1. Allez sur [GitHub Pull Requests](https://github.com/GoupilJeremy/agent-world/pulls).
2. Cliquez sur **New Pull Request**.
3. Sélectionnez :
   - **Base branch** : `main`
   - **Compare branch** : `feature/US-XXX`
4. Remplissez le **template de PR** :
   - **Titre** : `[feat] Ajouter dashboard VS Code (US-011)`
   - **Description** :
     ```markdown
     ## 📌 Description
     - Ajout du dashboard VS Code pour visualiser les agents.
     - Intégration avec l'API Agent World.
     
     ## 🎯 User Story
     - [US-011](https://github.com/GoupilJeremy/agent-world/blob/main/BACKLOG.md#us-011)
     
     ## ✅ Critères d'Acceptation
     - [x] Extension VS Code créée.
     - [x] Affichage des agents.
     - [x] Navigation basique.
     
     ## 🧪 Tests
     - [x] Tests unitaires ajoutés.
     - [x] Tests E2E validés.
     
     ## 📸 Captures d'Écran (si applicable)
     ![Dashboard VS Code](url)
     
     ## 🔗 Issues Liées
     - Closes #XXX
     ```
5. **Associez la PR à l'issue** : Utilisez `Closes #XXX` dans la description pour lier la PR à l'issue.

### **🔹 8. Attendre la Revue**
- Un **maintainer** reviendra votre PR sous 24-48h.
- **Corrigez les commentaires** si nécessaire.
- **Merguez la PR** une fois approuvée !

### **🔹 9. Célébrez ! 🎉**
- Votre contribution est maintenant partie d'Agent World !
- Partagez votre travail sur les réseaux sociaux avec le hashtag **#AgentWorld**.

---

## 📝 **Conventions de Code**

### **🔹 Python (Backend)**

#### **Style**
- Suivez les conventions [PEP 8](https://peps.python.org/pep-0008/).
- Utilisez **4 espaces** pour l'indentation (pas de tabulations).
- **Longueur des lignes** : 79 caractères (120 pour les docstrings).

#### **Nommage**
| **Type**               | **Convention**               | **Exemple**                          |
|------------------------|------------------------------|--------------------------------------|
| Variables/Fonctions    | `snake_case`                 | `get_agent_by_id()`                  |
| Classes                | `PascalCase`                 | `class AgentModel:`                  |
| Constantes             | `UPPER_SNAKE_CASE`          | `MAX_AGENTS = 100`                   |
| Modules/Fichiers       | `snake_case`                 | `agent_model.py`                     |

#### **Docstrings**
- Utilisez le format **Google** pour les docstrings :
  ```python
  def get_agent_by_id(agent_id: int) -> Agent:
      """Récupère un agent par son ID.
      
      Args:
          agent_id (int): L'ID de l'agent.
      
      Returns:
          Agent: L'agent correspondant.
      
      Raises:
          AgentNotFoundError: Si l'agent n'existe pas.
      """
      pass
  ```

#### **Typage**
- Utilisez les **type hints** pour toutes les fonctions :
  ```python
  def create_agent(name: str, model: str = "mistral") -> Agent:
      pass
  ```

#### **Gestion des Erreurs**
- Utilisez des **exceptions personnalisées** :
  ```python
  class AgentNotFoundError(Exception):
      pass
  ```
- **Ne pas utiliser** `try/except` silencieux (sauf pour des cas très spécifiques).

---

### **🔹 JavaScript/TypeScript (Frontend)**

#### **Style**
- Suivez les conventions [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).
- Utilisez **2 espaces** pour l'indentation.
- **Longueur des lignes** : 80 caractères.

#### **Nommage**
| **Type**               | **Convention**               | **Exemple**                          |
|------------------------|------------------------------|--------------------------------------|
| Variables/Fonctions    | `camelCase`                 | `getAgentById()`                     |
| Classes                | `PascalCase`                 | `class AgentModel {}`                |
| Constantes             | `UPPER_SNAKE_CASE`          | `const MAX_AGENTS = 100;`            |
| Fichiers               | `kebab-case`                 | `agent-model.tsx`                    |

#### **Typage (TypeScript)**
- Utilisez **TypeScript** pour le frontend.
- Définissez des **interfaces** pour les types complexes :
  ```typescript
  interface Agent {
    id: number;
    name: string;
    model: string;
    createdAt: Date;
  }
  ```

#### **Composants React**
- **Structure** :
  ```tsx
  // components/AgentCard.tsx
  import React from 'react';
  
  interface AgentCardProps {
    agent: Agent;
    onClick: () => void;
  }
  
  const AgentCard: React.FC<AgentCardProps> = ({ agent, onClick }) => {
    return (
      <div onClick={onClick}>
        <h2>{agent.name}</h2>
        <p>Model: {agent.model}</p>
      </div>
    );
  };
  
  export default AgentCard;
  ```
- **Nommage** : Utilisez `PascalCase` pour les composants.

---

### **🔹 SQL (Base de Données)**

#### **Nommage**
| **Type**               | **Convention**               | **Exemple**                          |
|------------------------|------------------------------|--------------------------------------|
| Tables                 | `snake_case` (pluriel)       | `agents`, `users`                    |
| Colonnes               | `snake_case`                 | `created_at`, `agent_name`           |
| Clés Primaires         | `id`                         | `id SERIAL PRIMARY KEY`             |
| Clés Étrangères         | `{table}_id`                 | `user_id`, `agent_id`                |

#### **Exemple de Table**
```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model VARCHAR(50) NOT NULL DEFAULT 'mistral',
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### **🔹 Git**

#### **Branches**
- **`main`** : Branche principale (stable).
- **`develop`** : Branche de développement (optionnelle, pour les gros projets).
- **`feature/*`** : Branches pour les nouvelles fonctionnalités.
- **`fix/*`** : Branches pour les corrections de bugs.
- **`docs/*`** : Branches pour la documentation.

#### **Messages de Commit**
- Utilisez [Conventional Commits](https://www.conventionalcommits.org/) :
  ```
  feat: ajouter dashboard VS Code (US-011)
  fix: corriger bug d'affichage des agents
  docs: mettre à jour le README
  refactor: simplifier la logique des agents
  chore: mettre à jour les dépendances
  ```

#### **Pull Requests**
- **Titre** : `[type] Description (US-XXX)` (ex: `[feat] Ajouter dashboard VS Code (US-011)`).
- **Description** : Utilisez le template fourni.
- **Lien vers l'issue** : Utilisez `Closes #XXX` pour lier la PR à l'issue.

---

## 🧪 **Tests**

### **🔹 Types de Tests**
| **Type**               | **Description**                                                                                     | **Outils**                          | **Exemple**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|--------------------------------------|
| **Tests Unitaires**    | Tester des fonctions ou méthodes individuellement.                                               | `pytest` (Python), `Jest` (JS)       | `test_agent_model.py`                |
| **Tests d'Intégration**| Tester l'interaction entre plusieurs composants.                                                | `pytest`, `supertest`                | `test_api_integration.py`            |
| **Tests E2E**          | Tester l'application de bout en bout (ex: flux utilisateur).                                     | `cypress`, `selenium`                | `test_e2e_agent_creation.py`         |

### **🔹 Exemples de Tests**

#### **Python (pytest)**
```python
# tests/test_agent_model.py
import pytest
from app.models.agent import Agent

@pytest.fixture
def sample_agent():
    return Agent(name="Test Agent", model="mistral")

def test_agent_creation(sample_agent):
    assert sample_agent.name == "Test Agent"
    assert sample_agent.model == "mistral"

def test_agent_run(sample_agent):
    result = sample_agent.run(input="Hello")
    assert isinstance(result, str)
    assert len(result) > 0
```

#### **JavaScript (Jest)**
```javascript
// tests/agentModel.test.js
const { Agent } = require('../models/Agent');

describe('Agent Model', () => {
  test('should create an agent', () => {
    const agent = new Agent({ name: 'Test Agent', model: 'mistral' });
    expect(agent.name).toBe('Test Agent');
    expect(agent.model).toBe('mistral');
  });

  test('should run an agent', async () => {
    const agent = new Agent({ name: 'Test Agent', model: 'mistral' });
    const result = await agent.run('Hello');
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });
});
```

### **🔹 Exécution des Tests**

#### **Backend (Python)**
```bash
# Installer pytest
pip install pytest

# Exécuter tous les tests
pytest

# Exécuter les tests avec couverture
pytest --cov=app --cov-report=html

# Exécuter un test spécifique
pytest tests/test_agent_model.py
```

#### **Frontend (JavaScript)**
```bash
# Installer Jest
npm install --save-dev jest

# Exécuter tous les tests
npm test

# Exécuter un test spécifique
npm test -- agentModel.test.js
```

#### **E2E (Cypress)**
```bash
# Installer Cypress
npm install --save-dev cypress

# Démarrer le serveur de test
npm run start:test

# Exécuter les tests E2E
npx cypress run
```

### **🔹 Couverture de Code**
- **Objectif** : **90% de couverture** pour le backend et le frontend.
- **Outils** :
  - Python : `pytest-cov`
  - JavaScript : `jest --coverage`

---

## 📜 **Documentation**

### **🔹 Règles de Documentation**
- **Langue** : Principalement en **français** (le projet est francophone).
- **Format** : **Markdown** (`.md`).
- **Style** : Clair, concis, avec des exemples.

### **🔹 Types de Documentation**
| **Type**               | **Description**                                                                                     | **Exemple**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **README.md**          | Documentation principale du projet.                                                             | [README.md](README.md)              |
| **Guides**             | Guides détaillés (installation, utilisation, etc.).                                               | [INSTALL.md](INSTALL.md)            |
| **API Documentation**  | Documentation de l'API (Swagger/OpenAPI).                                                          | `/api/docs`                          |
| **Tutoriels**          | Tutoriels pas-à-pas pour les utilisateurs.                                                        | `docs/tutorials/`                    |
| **FAQ**                | Foire aux questions.                                                                               | `docs/FAQ.md`                        |

### **🔹 Exemple de Documentation**

#### **Fonctionnalité**
```markdown
### 🔹 Créer un Agent

**Description** : Créer un nouvel agent IA avec un modèle spécifique.

**Requête** :
```bash
curl -X POST http://localhost:5000/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "Mon Agent", "model": "mistral"}'
```

**Réponse** :
```json
{
  "id": 123,
  "name": "Mon Agent",
  "model": "mistral",
  "created_at": "2026-08-06T10:00:00Z"
}
```

**Exemple (Python)** :
```python
import requests

response = requests.post(
    "http://localhost:5000/api/agents",
    json={"name": "Mon Agent", "model": "mistral"}
)
print(response.json())
```
```

---

## 🐛 **Signaler un Bug**

### **🔹 Avant de Signaler**
1. **Vérifiez les issues existantes** :
   - Allez sur [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues).
   - Utilisez la barre de recherche avec des mots-clés (ex: `bug`, `error`, `VS Code`).
2. **Testez avec la dernière version** :
   - Mettez à jour votre repository (`git pull origin main`).
   - Vérifiez si le bug est toujours présent.

### **🔹 Créer une Issue**
1. Cliquez sur **New Issue** sur [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues).
2. Utilisez le **template de bug** :
   ```markdown
   ## 🐛 Description du Bug
   Une description claire et concise du bug.
   
   ## 🔍 Étapes pour Reproduire
   1. Allez sur '...'
   2. Cliquez sur '...'
   3. Faites '...'
   4. Le bug apparaît.
   
   ## ✅ Comportement Attendu
   Ce qui devrait se passer.
   
   ## ❌ Comportement Actuel
   Ce qui se passe réellement.
   
   ## 📸 Captures d'Écran/Logs
   Ajoutez des captures d'écran ou des logs si applicable.
   
   ## 💻 Environnement
   - OS: [ex: Ubuntu 22.04]
   - Python: [ex: 3.10.12]
   - Node.js: [ex: 18.16.0]
   - Version d'Agent World: [ex: v0.2.0]
   
   ## 🔗 Issues Liées
   - #XXX
   ```
3. **Ajoutez des labels** :
   - `bug` : Pour les bugs.
   - `priority: high` : Si le bug est critique.
   - `component: [nom]` : Pour spécifier le composant (ex: `component: vs-code`, `component: api`).

---

## 💡 **Proposer une Fonctionnalité**

### **🔹 Avant de Proposer**
1. **Vérifiez le backlog** :
   - Consultez [BACKLOG.md](BACKLOG.md) pour voir si la fonctionnalité est déjà planifiée.
2. **Discutez-en** :
   - Ouvrez une **discussion** sur [GitHub Discussions](https://github.com/GoupilJeremy/agent-world/discussions) pour recueillir des avis.

### **🔹 Créer une Issue**
1. Cliquez sur **New Issue** sur [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues).
2. Utilisez le **template de fonctionnalité** :
   ```markdown
   ## 💡 Description de la Fonctionnalité
   Une description claire et détaillée de la fonctionnalité proposée.
   
   ## 🎯 Problème Résolu
   Quel problème cette fonctionnalité résout-elle ?
   
   ## ✅ Solution Proposée
   Comment implémenter cette fonctionnalité ?
   
   ## 📌 Exemples
   - Exemple 1 : ...
   - Exemple 2 : ...
   
   ## 🔗 Ressources
   - [Lien vers une documentation](url)
   - [Exemple similaire dans un autre projet](url)
   ```
3. **Ajoutez des labels** :
   - `enhancement` : Pour les nouvelles fonctionnalités.
   - `priority: low/medium/high` : Selon l'importance.
   - `epic: [nom]` : Si la fonctionnalité fait partie d'un épic (ex: `epic: vs-code`).

---

## 🤝 **Code de Conduite**

En participant à ce projet, vous acceptez de respecter notre **[Code de Conduite](CODE_OF_CONDUCT.md)**. Voici les principes clés :

- **Respect** : Soyez respectueux envers tous les membres de la communauté.
- **Inclusivité** : Encouragez la participation de tous, quel que soit leur niveau ou leur origine.
- **Collaboration** : Travaillez ensemble pour améliorer le projet.
- **Transparence** : Soyez transparent sur vos intentions et vos actions.
- **Responsabilité** : Prenez la responsabilité de vos contributions.

---

## 📊 **Bonnes Pratiques**

### **🔹 Développement**
- **Petits Commits** : Faites des commits **atomiques** (1 commit = 1 changement logique).
- **Tests** : Écrivez des tests pour **toute nouvelle fonctionnalité**.
- **Documentation** : Mettez à jour la documentation **en même temps** que le code.
- **Revue de Code** : Relisez votre code avant de pousser (ou utilisez `git add -p`).

### **🔹 Collaboration**
- **Communication** : Utilisez les **issues** et **discussions** pour poser des questions.
- **Feedback** : Donnez un **feedback constructif** lors des revues de code.
- **Aide** : Aidez les autres contributeurs si vous le pouvez.

### **🔹 Sécurité**
- **Ne commitez jamais** de secrets (clés API, mots de passe) dans le code.
- Utilisez `.gitignore` pour exclure les fichiers sensibles (ex: `.env`).
- Signalez les **vulnérabilités de sécurité** en privé à goupiljeremy@gmail.com.

---

## 🔗 **Ressources**

### **📚 Documentation**
- [Backlog](BACKLOG.md) : Détail des fonctionnalités.
- [Roadmap](ROADMAP.md) : Timeline et objectifs.
- [Changelog](CHANGELOG.md) : Historique des versions.
- [Installation](INSTALL.md) : Instructions détaillées.
- [Code de Conduite](CODE_OF_CONDUCT.md) : Règles de la communauté.

### **🛠️ Outils**
- **Repository** : [GoupilJeremy/agent-world](https://github.com/GoupilJeremy/agent-world)
- **Issues** : [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues)
- **Discussions** : [GitHub Discussions](https://github.com/GoupilJeremy/agent-world/discussions)
- **CI/CD** : [GitHub Actions](https://github.com/GoupilJeremy/agent-world/actions)

### **📢 Communication**
- **Email** : goupiljeremy@gmail.com
- **Discord** : [Lien à ajouter](https://discord.gg/)
- **Twitter** : [@AgentWorld](https://twitter.com/AgentWorld)

---

## 🙏 **Remerciements**

Merci à tous les contributeurs qui aident à faire d'**Agent World** un projet meilleur ! 🎉

Votre nom apparaîtra ici après votre première contribution.

---

*Document généré le 06 août 2026. Dernière mise à jour : [DATE]*
