# 📥 **Agent World - Guide d'Installation**
*Instructions détaillées pour installer et configurer Agent World*

---

## 📌 **Table des Matières**
1. [🎯 Prérequis](#-prérequis)
2. [📦 Installation Rapide](#-installation-rapide)
3. [🐳 Installation avec Docker](#-installation-avec-docker)
4. [🔧 Configuration Avancée](#-configuration-avancée)
5. [🚀 Démarrage](#-démarrage)
6. [✅ Vérification de l'Installation](#-vérification-de-linstallation)
7. [🛠️ Dépannage](#-dépannage)
8. [📜 Mise à Jour](#-mise-à-jour)
9. [🗃️ Désinstallation](#-désinstallation)

---

## 🎯 **Prérequis**

### **🔹 Système d'Exploitation**
Agent World est compatible avec :
- ✅ **Linux** (Ubuntu 20.04+, Debian 11+, Fedora 36+)
- ✅ **macOS** (11 Big Sur+)
- ✅ **Windows** (10/11 avec WSL2 recommandé)

> **⚠️ Note pour Windows** : Nous recommandons d'utiliser **WSL2** (Windows Subsystem for Linux) pour une meilleure compatibilité.

---

### **🔹 Logiciels Requises**

| **Logiciel**       | **Version Minimum** | **Vérification**                          | **Lien**                                  |
|--------------------|---------------------|-------------------------------------------|------------------------------------------|
| **Git**            | 2.30+               | `git --version`                          | [git-scm.com](https://git-scm.com/)      |
| **Python**         | 3.10+               | `python --version`                       | [python.org](https://www.python.org/)    |
| **Node.js**        | 18.x+               | `node --version`                         | [nodejs.org](https://nodejs.org/)        |
| **npm/yarn**       | 8.x+/1.22+          | `npm --version` ou `yarn --version`      | Inclus avec Node.js                      |
| **Docker**         | 20.x+               | `docker --version`                       | [docker.com](https://www.docker.com/)    |
| **Docker Compose** | 2.x+                | `docker-compose --version`               | Inclus avec Docker                       |

#### **Base de Données (au choix)**
| **Base de Données** | **Version Minimum** | **Vérification**                          | **Lien**                                  |
|--------------------|---------------------|-------------------------------------------|------------------------------------------|
| **PostgreSQL**     | 14+                 | `psql --version`                         | [postgresql.org](https://www.postgresql.org/) |
| **MongoDB**        | 6.0+                | `mongod --version`                        | [mongodb.com](https://www.mongodb.com/)   |
| **Redis**          | 6.x+                | `redis-cli --version`                     | [redis.io](https://redis.io/)            |

---

### **🔹 Espace Disque et Mémoire**
- **Espace disque** : ~2 Go (dépend des dépendances et de la base de données).
- **Mémoire RAM** : 4 Go minimum (8 Go recommandé pour le développement).

---

## 📦 **Installation Rapide**

### **🔹 1. Cloner le Repository**
```bash
# Cloner le repository
 git clone https://github.com/GoupilJeremy/agent-world.git

# Se déplacer dans le dossier
cd agent-world
```

---

### **🔹 2. Configurer l'Environnement Python**

#### **Créer un Environnement Virtuel**
```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Linux/macOS
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\activate

# Windows (CMD)
venv\Scripts\activate.bat
```

> **⚠️ Note** : Votre invite de commande doit maintenant afficher `(venv)` au début.

#### **Installer les Dépendances Backend**
```bash
# Mettre à jour pip
python -m pip install --upgrade pip

# Installer les dépendances
pip install -r requirements.txt

# Installer les dépendances de développement (optionnel)
pip install -r requirements-dev.txt
```

---

### **🔹 3. Configurer le Frontend (Optionnel)**

> **⚠️ Note** : Le frontend est optionnel si vous utilisez uniquement le CLI ou l'API.

```bash
# Se déplacer dans le dossier frontend
cd frontend

# Installer les dépendances
npm install

# Retourner à la racine
cd ..
```

---

### **🔹 4. Configurer les Variables d'Environnement**

#### **Créer un Fichier `.env`**
Créez un fichier `.env` à la racine du projet avec le contenu suivant :

```env
# =============================================================================
# Agent World - Configuration
# =============================================================================

# Environnement (development, production, test)
FLASK_ENV=development
SECRET_KEY=votre_clé_secrète_ici

# Base de Données (choisissez une option)
# Option 1 : PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/agent_world

# Option 2 : MongoDB
# DATABASE_URL=mongodb://localhost:27017/agent_world

# Option 3 : SQLite (pour le développement)
# DATABASE_URL=sqlite:///agent_world.db

# =============================================================================
# Modèles IA
# =============================================================================
# Mistral
MISTRAL_API_KEY=votre_clé_api_mistral
MISTRAL_API_URL=https://api.mistral.ai

# OpenAI
OPENAI_API_KEY=votre_clé_api_openai
OPENAI_API_URL=https://api.openai.com

# Anthropic
ANTHROPIC_API_KEY=votre_clé_api_anthropic
ANTHROPIC_API_URL=https://api.anthropic.com

# =============================================================================
# Frontend (si applicable)
# =============================================================================
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENV=development

# =============================================================================
# VS Code Extension (si applicable)
# =============================================================================
AGENT_WORLD_API_URL=http://localhost:5000
```

#### **Générer une Clé Secrète**
Pour générer une clé secrète pour `SECRET_KEY` :
```bash
# Linux/macOS
python -c "import secrets; print(secrets.token_hex(32))"

# Windows
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### **🔹 5. Initialiser la Base de Données**

#### **Option 1 : PostgreSQL**
1. **Installer PostgreSQL** :
   - **Linux (Ubuntu/Debian)** :
     ```bash
     sudo apt update
     sudo apt install postgresql postgresql-contrib
     ```
   - **macOS (Homebrew)** :
     ```bash
     brew install postgresql
     ```
   - **Windows** : Téléchargez depuis [postgresql.org](https://www.postgresql.org/download/).

2. **Créer un Utilisateur et une Base de Données** :
   ```bash
   # Se connecter à PostgreSQL
   sudo -u postgres psql
   
   # Créer un utilisateur
   CREATE USER agent_world_user WITH PASSWORD 'votre_mot_de_passe';
   
   # Créer une base de données
   CREATE DATABASE agent_world;
   
   # Donner les permissions
   GRANT ALL PRIVILEGES ON DATABASE agent_world TO agent_world_user;
   
   # Quitter
   \q
   ```

3. **Mettre à jour `.env`** :
   ```env
   DATABASE_URL=postgresql://agent_world_user:votre_mot_de_passe@localhost:5432/agent_world
   ```

4. **Initialiser la Base de Données** :
   ```bash
   # Installer Flask-Migrate (si ce n'est pas déjà fait)
   pip install flask-migrate
   
   # Initialiser les migrations
   flask db init
   
   # Créer une migration
   flask db migrate -m "Initial migration"
   
   # Appliquer les migrations
   flask db upgrade
   ```

#### **Option 2 : MongoDB**
1. **Installer MongoDB** :
   - **Linux (Ubuntu/Debian)** :
     ```bash
     sudo apt update
     sudo apt install mongodb
     sudo systemctl start mongodb
     ```
   - **macOS (Homebrew)** :
     ```bash
     brew tap mongodb/brew
     brew install mongodb-community
     brew services start mongodb-community
     ```
   - **Windows** : Téléchargez depuis [mongodb.com](https://www.mongodb.com/try/download/community).

2. **Mettre à jour `.env`** :
   ```env
   DATABASE_URL=mongodb://localhost:27017/agent_world
   ```

3. **Initialiser la Base de Données** :
   ```bash
   python scripts/init_mongo.py
   ```

#### **Option 3 : SQLite (pour le développement)**
1. **Mettre à jour `.env`** :
   ```env
   DATABASE_URL=sqlite:///agent_world.db
   ```

2. **Initialiser la Base de Données** :
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

---

## 🐳 **Installation avec Docker**

### **🔹 Prérequis**
- Docker 20.x+
- Docker Compose 2.x+

---

### **🔹 1. Cloner le Repository**
```bash
git clone https://github.com/GoupilJeremy/agent-world.git
cd agent-world
```

---

### **🔹 2. Configurer les Variables d'Environnement**
Créez un fichier `.env.docker` à la racine du projet :

```env
# =============================================================================
# Agent World - Configuration Docker
# =============================================================================

# Environnement
FLASK_ENV=development
SECRET_KEY=votre_clé_secrète_ici

# Base de Données (PostgreSQL)
POSTGRES_USER=agent_world_user
POSTGRES_PASSWORD=votre_mot_de_passe
POSTGRES_DB=agent_world
DATABASE_URL=postgresql://agent_world_user:votre_mot_de_passe@db:5432/agent_world

# Modèles IA
MISTRAL_API_KEY=votre_clé_api_mistral
OPENAI_API_KEY=votre_clé_api_openai

# Frontend
REACT_APP_API_URL=http://backend:5000
```

---

### **🔹 3. Construire et Démarrer les Conteneurs**
```bash
# Construire les images
 docker-compose build

# Démarrer les conteneurs
 docker-compose up -d
```

---

### **🔹 4. Vérifier les Conteneurs**
```bash
# Lister les conteneurs en cours d'exécution
docker-compose ps

# Voir les logs
docker-compose logs -f
```

---

### **🔹 5. Accéder à l'Application**
- **Backend** : [http://localhost:5000](http://localhost:5000)
- **Frontend** : [http://localhost:3000](http://localhost:3000)
- **Base de Données (PostgreSQL)** : `localhost:5432` (utilisateur : `agent_world_user`, mot de passe : `votre_mot_de_passe`)
- **Redis** : `localhost:6379`

---

### **🔹 6. Arrêter les Conteneurs**
```bash
# Arrêter les conteneurs
docker-compose down

# Arrêter et supprimer les volumes (attention : perte de données !)
docker-compose down -v
```

---

## 🔧 **Configuration Avancée**

### **🔹 Configurer Plusieurs Modèles IA**
Vous pouvez configurer plusieurs modèles IA dans `.env` :

```env
# Mistral
MISTRAL_API_KEY=votre_clé_api_mistral
MISTRAL_API_URL=https://api.mistral.ai

# OpenAI
OPENAI_API_KEY=votre_clé_api_openai
OPENAI_API_URL=https://api.openai.com

# Anthropic
ANTHROPIC_API_KEY=votre_clé_api_anthropic
ANTHROPIC_API_URL=https://api.anthropic.com

# Llama (via Ollama)
OLLAMA_API_URL=http://localhost:11434
```

---

### **🔹 Configurer Redis pour le Cache**
1. **Installer Redis** :
   - **Linux (Ubuntu/Debian)** :
     ```bash
     sudo apt update
     sudo apt install redis-server
     sudo systemctl start redis
     ```
   - **macOS (Homebrew)** :
     ```bash
     brew install redis
     brew services start redis
     ```
   - **Windows** : Utilisez WSL ou Docker.

2. **Mettre à jour `.env`** :
   ```env
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Installer les dépendances Redis** :
   ```bash
   pip install redis
   ```

---

### **🔹 Configurer HTTPS (pour la production)**
Pour activer HTTPS en production :

1. **Installer Certbot** (pour Let's Encrypt) :
   ```bash
   sudo apt update
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Obtenir un Certificat SSL** :
   ```bash
   sudo certbot --nginx -d votre-domaine.com
   ```

3. **Mettre à jour `.env`** :
   ```env
   FLASK_ENV=production
   SSL_CERT=/etc/letsencrypt/live/votre-domaine.com/fullchain.pem
   SSL_KEY=/etc/letsencrypt/live/votre-domaine.com/privkey.pem
   ```

---

## 🚀 **Démarrage**

### **🔹 Démarrer le Backend**
```bash
# Activer l'environnement virtuel (si ce n'est pas déjà fait)
source venv/bin/activate  # Linux/macOS

# Démarrer le serveur Flask
flask run
```

> **⚠️ Note** : Par défaut, le serveur démarrera sur `http://localhost:5000`.

---

### **🔹 Démarrer le Frontend**
```bash
# Se déplacer dans le dossier frontend
cd frontend

# Démarrer l'application React
npm start
```

> **⚠️ Note** : Le frontend démarrera sur `http://localhost:3000`.

---

### **🔹 Démarrer avec Docker**
```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les services
docker-compose ps
```

---

## ✅ **Vérification de l'Installation**

### **🔹 Tester le Backend**
1. **Vérifier que le serveur est en cours d'exécution** :
   ```bash
   curl http://localhost:5000/api/health
   ```
   **Réponse attendue** :
   ```json
   {
     "status": "healthy",
     "version": "0.2.0"
   }
   ```

2. **Tester l'API** :
   ```bash
   # Lister les agents
   curl http://localhost:5000/api/agents
   
   # Créer un agent
   curl -X POST http://localhost:5000/api/agents \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Agent", "model": "mistral"}'
   ```

---

### **🔹 Tester le Frontend**
1. Ouvrez votre navigateur et allez sur [http://localhost:3000](http://localhost:3000).
2. Vous devriez voir l'interface d'Agent World.

---

### **🔹 Tester le CLI**
```bash
# Lister les agents
python -m app.cli list

# Créer un agent
python -m app.cli create --name "Mon Agent" --model mistral

# Exécuter un agent
python -m app.cli run 1 --input "Bonjour !"
```

---

## 🛠️ **Dépannage**

### **🔹 Problèmes Courants**

#### **1. Erreur : `ModuleNotFoundError: No module named 'flask'`**
**Cause** : Les dépendances Python ne sont pas installées.
**Solution** :
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

#### **2. Erreur : `Could not connect to PostgreSQL`**
**Cause** : PostgreSQL n'est pas en cours d'exécution ou les identifiants sont incorrects.
**Solution** :
```bash
# Vérifier que PostgreSQL est en cours d'exécution
sudo systemctl status postgresql

# Redémarrer PostgreSQL
sudo systemctl restart postgresql

# Vérifier les identifiants dans .env
DATABASE_URL=postgresql://user:password@localhost:5432/agent_world
```

---

#### **3. Erreur : `Port 5000 is already in use`**
**Cause** : Un autre service utilise le port 5000.
**Solution** :
```bash
# Trouver le processus utilisant le port 5000
sudo lsof -i :5000

# Tuer le processus (remplacez PID par l'ID du processus)
kill -9 PID

# Ou démarrer Flask sur un autre port
flask run --port 5001
```

---

#### **4. Erreur : `npm ERR! missing script: "start"`**
**Cause** : Les dépendances Node.js ne sont pas installées.
**Solution** :
```bash
cd frontend
npm install
cd ..
```

---

#### **5. Erreur : `Docker: permission denied`**
**Cause** : L'utilisateur actuel n'a pas les permissions pour Docker.
**Solution** :
```bash
# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Redémarrer la session
newgrp docker

# Vérifier
 docker run hello-world
```

---

#### **6. Erreur : `API key not found`**
**Cause** : Les clés API pour les modèles IA ne sont pas configurées.
**Solution** :
1. Obtenez une clé API depuis [Mistral](https://mistral.ai/) ou [OpenAI](https://openai.com/).
2. Mettez à jour `.env` :
   ```env
   MISTRAL_API_KEY=votre_clé_api_mistral
   OPENAI_API_KEY=votre_clé_api_openai
   ```

---

### **🔹 Logs et Debugging**

#### **Backend (Flask)**
```bash
# Activer le mode debug
flask run --debug

# Voir les logs
flask logs
```

#### **Frontend (React)**
```bash
# Démarrer avec des logs détaillés
npm start -- --verbose
```

#### **Docker**
```bash
# Voir les logs de tous les conteneurs
docker-compose logs -f

# Voir les logs d'un conteneur spécifique
docker-compose logs -f backend
```

---

## 📜 **Mise à Jour**

### **🔹 Mettre à Jour le Code**
```bash
# Se déplacer dans le repository
cd agent-world

# Tirer les dernières modifications
git pull origin main

# Mettre à jour les dépendances Python
pip install -r requirements.txt

# Mettre à jour les dépendances Node.js (si frontend)
cd frontend
npm install
cd ..
```

---

### **🔹 Mettre à Jour Docker**
```bash
# Tirer les dernières modifications
git pull origin main

# Reconstruire les images
docker-compose build --no-cache

# Redémarrer les conteneurs
docker-compose up -d
```

---

## 🗃️ **Désinstallation**

### **🔹 Désinstaller l'Installation Locale**
```bash
# Désactiver l'environnement virtuel
deactivate

# Supprimer l'environnement virtuel
rm -rf venv

# Supprimer les dépendances Node.js (si frontend)
cd frontend
rm -rf node_modules package-lock.json
cd ..

# Supprimer le repository
cd ..
rm -rf agent-world
```

---

### **🔹 Désinstaller Docker**
```bash
# Arrêter et supprimer les conteneurs
docker-compose down -v

# Supprimer les images
docker rmi agent-world_backend agent-world_frontend

# Supprimer les volumes (attention : perte de données !)
docker volume prune
```

---

## 🔗 **Ressources**

### **📚 Documentation**
- [README](README.md) : Documentation principale.
- [BACKLOG](BACKLOG.md) : Détail des fonctionnalités.
- [ROADMAP](ROADMAP.md) : Timeline et objectifs.
- [CONTRIBUTING](CONTRIBUTING.md) : Guide pour contribuer.

### **🛠️ Outils**
- **Repository** : [GoupilJeremy/agent-world](https://github.com/GoupilJeremy/agent-world)
- **Issues** : [GitHub Issues](https://github.com/GoupilJeremy/agent-world/issues)
- **Discussions** : [GitHub Discussions](https://github.com/GoupilJeremy/agent-world/discussions)

### **📢 Communication**
- **Email** : goupiljeremy@gmail.com
- **Discord** : [Lien à ajouter](https://discord.gg/)
- **Twitter** : [@AgentWorld](https://twitter.com/AgentWorld)

---

## 🙏 **Remerciements**

Merci d'avoir installé **Agent World** ! 🎉

Si vous rencontrez des problèmes, n'hésitez pas à :
1. Consulter les [issues ouvertes](https://github.com/GoupilJeremy/agent-world/issues).
2. Ouvrir une nouvelle issue avec une description détaillée.
3. Rejoindre notre communauté sur [Discord](https://discord.gg/).

---

*Document généré le 06 août 2026. Dernière mise à jour : [DATE]*
