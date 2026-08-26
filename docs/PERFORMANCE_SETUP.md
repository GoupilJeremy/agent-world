# 🚀 Agent World - Performance Setup Guide

**Version** : 0.4.2  
**Épic** : [Épic 8 - Performance et Scalabilité](file:///c:/dev/agent-world/agent-world/BACKLOG.md#pics-épic-8--performance-et-scalabilité)  
**Date** : 26 août 2026  

---

## 📋 **Table des Matières**

1. [🎯 Introduction](#-introduction)
2. [📦 Prérequis](#-prérequis)
3. [🔧 Configuration de Redis](#-configuration-de-redis)
4. [🗃️ Optimisation de la Base de Données](#-optimisation-de-la-base-de-données)
5. [📊 Monitoring avec Prometheus et Grafana](#-monitoring-avec-prometheus-et-grafana)
6. [⚡ Optimisation des Requêtes API](#-optimisation-des-requêtes-api)
7. [🧪 Tests de Performance](#-tests-de-performance)
8. [🎛️ Scripts d'Optimisation](#-scripts-doptimisation)
9. [📊 Métriques et KPIs](#-métriques-et-kpis)
10. [🔒 Sécurité et Bonnes Pratiques](#-sécurité-et-bonnes-pratiques)
11. [🚨 Résolution des Problèmes](#-résolution-des-problèmes)

---

## 🎯 **Introduction**

Ce guide explique comment configurer et utiliser les fonctionnalités de performance implémentées dans **l'Épic 8** :

- **Cache Redis** : Réduction de la latence des requêtes API
- **Pagination** : Optimisation des endpoints retournant des listes
- **Cache des résultats des agents** : Éviter les recalculs inutiles
- **Optimisation de la base de données** : Index et analyse des requêtes lentes
- **Monitoring** : Intégration avec Prometheus et Grafana

---

## 📦 **Prérequis**

### **Logiciels Requises**

| Logiciel | Version Recommandée | Description |
|----------|---------------------|-------------|
| Python | 3.10+ | Nécessaire pour l'application |
| Redis | 7.x | Pour le cache |
| PostgreSQL | 14+ | Base de données principale |
| Docker | 20.x | Pour le déploiement conteneurisé |
| Docker Compose | 2.x | Pour l'orchestration |
| Prometheus | 2.x | Pour le monitoring (optionnel) |
| Grafana | 10.x | Pour la visualisation (optionnel) |

### **Dépendances Python**

Les dépendances sont déjà incluses dans `requirements.txt` :
```bash
redis==5.0.1
flask-caching==2.1.0  # Optionnel, peut être ajouté
```

---

## 🔧 **Configuration de Redis**

### **Option 1 : Installation locale (Développement)**

#### Sur Ubuntu/Debian
```bash
# Installer Redis
sudo apt update
sudo apt install redis-server

# Démarrer Redis
sudo systemctl start redis

# Activer au démarrage
sudo systemctl enable redis

# Vérifier le statut
sudo systemctl status redis
redis-cli ping  # Doit retourner "PONG"
```

#### Sur macOS (avec Homebrew)
```bash
brew install redis
brew services start redis
redis-cli ping
```

#### Sur Windows
Télécharger et installer Redis depuis [Microsoft's port](https://github.com/microsoftarchive/redis/releases).

### **Option 2 : Avec Docker (Recommandé)**

Utiliser le fichier `docker-compose.performance.yml` :

```bash
# Démarrer Redis avec Docker Compose
docker-compose -f docker-compose.performance.yml up -d redis

# Vérifier que Redis est en cours d'exécution
docker ps | grep redis

# Tester la connexion
docker exec -it agent_world_redis redis-cli ping
```

### **Option 3 : Service Managé (Production)**

Pour la production, utilisez un service Redis managé :

- **Redis Labs** : [https://redis.com/try-free/](https://redis.com/try-free/)
- **AWS ElastiCache** : [https://aws.amazon.com/elasticache/](https://aws.amazon.com/elasticache/)
- **Azure Cache for Redis** : [https://azure.microsoft.com/fr-fr/products/cache/](https://azure.microsoft.com/fr-fr/products/cache/)

### **Configuration dans Agent World**

Ajouter les variables d'environnement dans votre fichier `.env` :

```bash
# Configuration Redis
REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=3600  # 1 heure par défaut
```

Pour un Redis avec authentification :
```bash
REDIS_URL=redis://username:password@localhost:6379/0
```

### **Test de la Connexion Redis**

```bash
# Avec le script Python
python scripts/optimize_performance.py --check

# Ou manuellement avec redis-cli
redis-cli -h localhost -p 6379 ping
```

---

## 🗃️ **Optimisation de la Base de Données**

### **Création des Index Manquants**

Les index optimisés pour les tables principales sont définis dans la migration `20260826_0004_epic8_performance.py`.

#### Méthode 1 : Utiliser Alembic

```bash
# Mettre à jour la base de données avec les nouveaux index
flask db upgrade

# Ou spécifiquement pour la migration de performance
flask db upgrade 20260826_0004
```

#### Méthode 2 : Utiliser le Script d'Optimisation

```bash
# Vérifier les index manquants
python scripts/optimize_performance.py --indexes

# Créer les index manquants (avec confirmation)
python scripts/optimize_performance.py --indexes --yes
```

#### Méthode 3 : Manuellement

Connectez-vous à votre base de données et exécutez :

```sql
-- Pour PostgreSQL
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at);
CREATE INDEX IF NOT EXISTS idx_executions_agent_id ON executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
-- ... (voir la migration pour la liste complète)
```

### **Exécution de VACUUM ANALYZE (PostgreSQL)**

```bash
# Exécuter VACUUM ANALYZE sur toutes les tables
python scripts/optimize_performance.py --vacuum --yes

# Ou manuellement dans psql
VACUUM ANALYZE;
```

### **Activation de pg_stat_statements (PostgreSQL)**

Pour analyser les requêtes lentes :

```sql
-- Créer l'extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Voir les requêtes lentes (> 100ms)
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 20;
```

---

## 📊 **Monitoring avec Prometheus et Grafana**

### **Déploiement avec Docker Compose**

```bash
# Démarrer tous les services de monitoring
docker-compose -f docker-compose.performance.yml up -d prometheus grafana

# Accéder aux interfaces
# Prometheus : http://localhost:9090
# Grafana : http://localhost:3000 (admin/agentworld)
```

### **Configuration de Prometheus**

Le fichier `monitoring/prometheus.yml` contient la configuration de base. Pour ajouter le monitoring de l'application Flask :

1. Installer `prometheus_flask_exporter` :
```bash
pip install prometheus-flask-exporter
```

2. Modifier `backend/app.py` pour activer les métriques :
```python
from prometheus_flask_exporter import PrometheusMetrics

# Dans create_app()
metrics = PrometheusMetrics(app)
metrics.info('agent_world_info', 'Application info', version='0.4.2')
```

### **Configuration de Grafana**

1. Importer un dashboard existant pour Flask/Redis/PostgreSQL
2. Ou créer un dashboard personnalisé avec les métriques suivantes :
   - `flask_http_request_duration_seconds` (Latence des requêtes)
   - `flask_http_request_total` (Nombre de requêtes)
   - `redis_memory_used_bytes` (Mémoire Redis utilisée)
   - `redis_commands_processed_total` (Commandes Redis traitées)

---

## ⚡ **Optimisation des Requêtes API**

### **Cache des Réponses API**

Le décorateur `@cache_response` permet de mettre en cache les réponses des endpoints :

```python
from backend.services.cache_service import cache_response

class MyResource(Resource):
    @cache_response(timeout=300, key_prefix="my_endpoint:")
    def get(self):
        # Ce code ne sera exécuté que si le cache est vide
        return {"data": "expensive_query_result"}
```

**Paramètres** :
- `timeout` : Durée de vie du cache en secondes (défaut : 3600)
- `key_prefix` : Préfixe pour la clé de cache (défaut : "api:")

### **Invalidation du Cache**

Utilisez le décorateur `@invalidate_cache` pour invalider le cache après une modification :

```python
from backend.services.cache_service import invalidate_cache

class MyResource(Resource):
    @invalidate_cache(key_prefix="my_endpoint:")
    def post(self):
        # Créer ou modifier une ressource
        return {"status": "created"}
```

### **Pagination**

La pagination est automatiquement disponible sur les endpoints utilisant `PaginationService` :

```bash
# Requête avec pagination
GET /api/agents?page=1&per_page=10

# Réponse
{
  "items": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 10,
    "total_pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

**Paramètres** :
- `page` : Numéro de page (1-based, défaut : 1)
- `per_page` : Nombre d'éléments par page (max : 100, défaut : 20)

### **Cache des Résultats des Agents**

Le service `AgentCacheService` permet de mettre en cache les résultats des exécutions d'agents :

```python
from backend.services.agent_cache_service import get_agent_cache_service

agent_cache = get_agent_cache_service()

# Mettre en cache un résultat
agent_cache.cache_execution_result(
    agent_id=1,
    input_data={"text": "Hello"},
    result={"output": "Bonjour"},
    model="mistral-tiny",
    ttl=3600
)

# Récupérer un résultat depuis le cache
cached_result = agent_cache.get_execution_result(
    agent_id=1,
    input_data={"text": "Hello"},
    model="mistral-tiny"
)
```

---

## 🧪 **Tests de Performance**

### **Exécution des Tests**

```bash
# Tous les tests de performance
pytest backend/tests/test_performance.py -v

# Tests spécifiques
pytest backend/tests/test_performance.py::TestCacheService -v
pytest backend/tests/test_performance.py::TestPaginationService -v

# Tests de stress (lents)
pytest backend/tests/test_performance.py::TestStressTests -v --mark slow
```

### **Benchmark Manuel**

Utiliser `locust` pour les tests de charge :

1. Installer Locust :
```bash
pip install locust
```

2. Créer un fichier `locustfile.py` :
```python
from locust import HttpUser, task, between

class AgentWorldUser(HttpUser):
    wait_time = between(0.5, 2.5)

    @task
    def get_agents(self):
        self.client.get("/api/agents?page=1&per_page=20")

    @task(3)
    def get_agent(self):
        self.client.get("/api/agents/1")
```

3. Exécuter Locust :
```bash
locust -f locustfile.py --headless -u 100 -r 10 -H http://localhost:5000
```

---

## 🎛️ **Scripts d'Optimisation**

### **Script Principal : `optimize_performance.py`**

```bash
# Voir l'aide
python scripts/optimize_performance.py --help

# Vérifier l'état de la performance
python scripts/optimize_performance.py --check

# Exécuter toutes les optimisations
python scripts/optimize_performance.py --all --yes

# Générer un rapport
python scripts/optimize_performance.py --report performance_report.json

# Créer les index manquants
python scripts/optimize_performance.py --indexes --yes

# Exécuter VACUUM ANALYZE
python scripts/optimize_performance.py --vacuum --yes
```

### **Options du Script**

| Option | Description |
|--------|-------------|
| `--check` | Vérifie l'état (Redis, index BDD) |
| `--optimize` | Exécute toutes les optimisations |
| `--indexes` | Crée les index manquants |
| `--vacuum` | Exécute VACUUM ANALYZE |
| `--report FILE` | Génère un rapport dans un fichier |
| `--test-endpoints` | Test les endpoints de performance |
| `--all` | Exécute toutes les opérations |
| `--yes` | Répond "oui" à toutes les confirmations |
| `--verbose` | Active le mode verbeux |

---

## 📊 **Métriques et KPIs**

### **Objectifs de Performance**

| Métrique | Valeur Actuelle | Objectif Épic 8 | Statut |
|----------|-----------------|-----------------|--------|
| Temps de réponse API (moyen) | ~500ms | < 150ms | ⏳ |
| Taux de cache hit | 0% | > 85% | ⏳ |
| Requêtes simultanées supportées | ~50 | > 500 | ⏳ |
| Temps de réponse BDD | ~200ms | < 80ms | ⏳ |

### **Endpoints de Monitoring**

| Endpoint | Description |
|----------|-------------|
| `GET /api/performance/cache/stats` | Statistiques du cache |
| `POST /api/performance/cache/clear` | Vider le cache |
| `GET /api/performance/db/optimize` | Rapport d'optimisation BDD |
| `POST /api/performance/db/indexes` | Créer les index manquants |
| `GET /api/performance/db/stats` | Statistiques des tables |
| `POST /api/performance/db/vacuum` | Exécuter VACUUM ANALYZE |

### **Exemple de Réponse : Cache Stats**

```json
{
  "available": true,
  "agent_cache": {
    "available": true,
    "agent_result_keys": 42,
    "agent_metadata_keys": 5,
    "total_agent_keys": 47,
    "redis_info": {
      "used_memory": "1.23M",
      "connected_clients": 1,
      "uptime": 86400
    }
  },
  "redis_info": {
    "used_memory_human": "1.23M",
    "connected_clients": 1,
    "uptime_in_seconds": 86400,
    "total_commands_processed": 1000,
    "keys": {
      "total": 150,
      "expires": 50
    }
  }
}
```

---

## 🔒 **Sécurité et Bonnes Pratiques**

### **Sécurité Redis**

1. **Ne jamais exposer Redis sur Internet sans authentification**
2. Activer le mot de passe :
   ```bash
   # Dans redis.conf
   requirepass your_strong_password
   ```
3. Limiter les connexions :
   ```bash
   # Dans redis.conf
   maxclients 10000
   maxmemory 2gb
   maxmemory-policy allkeys-lru
   ```
4. Activer le chiffrement TLS pour Redis Cloud

### **Sauvegarde des Données**

1. **Redis** : Configurer la persistance AOF/RDB
   ```bash
   # Dans redis.conf
   appendonly yes
   save 900 1
   save 300 10
   save 60 10000
   ```

2. **PostgreSQL** : Sauvegardes régulières
   ```bash
   # Sauvegarde quotidienne
   pg_dump -U postgres -d agent_world -F c -f backup_$(date +%Y%m%d).dump
   ```

### **Bonnes Pratiques de Cache**

1. Toujours définir un TTL (Time To Live) pour les clés de cache
2. Utiliser des préfixes pour organiser les clés
3. Invalider le cache après les modifications
4. Ne pas mettre en cache les données sensibles
5. Surveiller l'utilisation de la mémoire Redis

---

## 🚨 **Résolution des Problèmes**

### **Problèmes Courants**

#### Redis ne démarre pas

```bash
# Vérifier les logs Redis
docker logs agent_world_redis

# Tester la connexion
redis-cli -h localhost -p 6379 ping

# Si le port est déjà utilisé
sudo lsof -i :6379
sudo kill -9 <PID>
```

#### Les index ne sont pas créés

```bash
# Vérifier les tables existantes
psql -U postgres -d agent_world -c "\dt"

# Vérifier les index existants
psql -U postgres -d agent_world -c "\di"

# Exécuter manuellement la migration
flask db upgrade
```

#### Problèmes de connexion Redis dans l'application

```bash
# Vérifier la configuration
python -c "from backend.app import create_app; app = create_app(); print(app.config.get('REDIS_URL'))"

# Tester la connexion Redis directement
python -c "import redis; r = redis.Redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

#### La pagination ne fonctionne pas

```bash
# Vérifier que les paramètres sont passés
curl -v "http://localhost:5000/api/agents?page=1&per_page=10"

# Vérifier les logs de l'application
# Les erreurs doivent apparaître dans les logs Flask
```

---

## 📚 **Ressources Supplémentaires**

- [Redis Documentation](https://redis.io/docs/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Flask-Caching Documentation](https://pythonhosted.org/Flask-Caching/)

---

## 🏷️ **Tags et Versions**

- **Épic** : 8
- **Version** : 0.4.2
- **Date** : 26 août 2026
- **Auteur** : Jereg (Agent World Team)
- **Statut** : ✅ Implémenté

---

*Document généré pour l'Épic 8 - Performance et Scalabilité*
