# 🐳 Agent World - Kubernetes Configuration

**Version** : 0.4.3 (Épic 8 - Sprint 6)  
**Description** : Configuration Kubernetes pour le déploiement scalable de Agent World  

---

## 📌 **Structure**

```
kubernetes/
├── backend/
│   ├── deployment.yaml      # Déploiement du backend
│   ├── service.yaml         # Service backend
│   ├── ingress.yaml         # Ingress pour le routing
│   ├── hpa.yaml             # Horizontal Pod Autoscaler
│   ├── configmap.yaml       # Configuration de l'application
│   └── secret.yaml          # Secrets (à ne pas commiter)
├── redis/
│   ├── deployment.yaml      # Déploiement Redis
│   ├── service.yaml         # Service Redis
│   └── pvc.yaml             # Persistent Volume Claim
├── postgres/
│   ├── deployment.yaml      # Déploiement PostgreSQL
│   ├── service.yaml         # Service PostgreSQL
│   └── pvc.yaml             # Persistent Volume Claim
├── monitoring/
│   ├── prometheus.yaml      # Déploiement Prometheus
│   ├── grafana.yaml         # Déploiement Grafana
│   └── service-monitor.yaml # ServiceMonitor pour Prometheus
└── kustomization.yaml       # Kustomize pour le déploiement
```

---

## 🚀 **Prérequis**

1. **Cluster Kubernetes** :
   - Minikube (développement)
   - EKS (AWS)
   - GKE (Google Cloud)
   - AKS (Azure)

2. **Outils** :
   - `kubectl` (v1.25+)
   - `kubectx` (optionnel, pour gérer les contextes)
   - `kustomize` (v4.5+)
   - `helm` (v3.10+, optionnel)

3. **Stockage** :
   - StorageClass configuré pour les Persistent Volumes
   - Suffisamment d'espace pour Redis et PostgreSQL

---

## 📦 **Déploiement**

### **Option 1 : Avec Kustomize (Recommandé)**

```bash
# Aller dans le dossier kubernetes
cd kubernetes

# Appliquer toute la configuration
kubectl apply -k .

# Vérifier le déploiement
kubectl get pods -n agent-world
kubectl get services -n agent-world
kubectl get ingress -n agent-world
```

### **Option 2 : Avec Helm (Alternative)**

```bash
# Installer le chart (à créer)
helm install agent-world ./charts/agent-world

# Mettre à jour
helm upgrade agent-world ./charts/agent-world
```

### **Option 3 : Fichiers individuels**

```bash
# Créer le namespace
kubectl create namespace agent-world

# Déployer Redis
kubectl apply -f redis/

# Déployer PostgreSQL
kubectl apply -f postgres/

# Déployer le backend
kubectl apply -f backend/

# Déployer le monitoring (optionnel)
kubectl apply -f monitoring/
```

---

## 🔧 **Configuration**

### **Backend Configuration**

Le `ConfigMap` et `Secret` contiennent la configuration de l'application.

#### **ConfigMap (configmap.yaml)**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-world-config
  namespace: agent-world
data:
  FLASK_ENV: "production"
  SQLALCHEMY_DATABASE_URI: "postgresql://postgres:$(POSTGRES_PASSWORD)@postgres:5432/agent_world"
  REDIS_URL: "redis://redis:6379/0"
  CACHE_DEFAULT_TIMEOUT: "3600"
  OUTPUT_DIR: "/app/outputs"
  LOG_LEVEL: "INFO"
```

#### **Secret (secret.yaml)**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent-world-secrets
  namespace: agent-world
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key-here"
  POSTGRES_PASSWORD: "your-postgres-password"
  MISTRAL_API_KEY: "your-mistral-api-key"
  OPENAI_API_KEY: "your-openai-api-key"
```

> ⚠️ **Ne jamais commiter le fichier secret.yaml dans le repository !**
> Utiliser `kubectl create secret` ou un outil comme `sealed-secrets`.

---

## ⚖️ **Scalabilité**

### **Horizontal Pod Autoscaler (HPA)**

Le HPA ajuste automatiquement le nombre de pods en fonction de la charge CPU :

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: agent-world
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

**Commandes utiles** :
```bash
# Voir le HPA
kubectl get hpa -n agent-world

# Voir les métriques
kubectl top pods -n agent-world

# Scaler manuellement
kubectl scale deployment backend --replicas=5 -n agent-world
```

### **Load Balancing**

Le `Service` de type `LoadBalancer` ou l'`Ingress` avec un contrôleur comme Nginx ou Traefik permet de répartir la charge :

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: agent-world
spec:
  selector:
    app: backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: LoadBalancer
```

---

## 📊 **Monitoring**

### **Prometheus + Grafana**

Le dossier `monitoring/` contient les configurations pour :
- Prometheus (scraping des métriques)
- Grafana (visualisation)
- ServiceMonitor (découverte automatique)

**Installation** :
```bash
# Installer Prometheus Operator (si ce n'est pas déjà fait)
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup.yaml
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/

# Déployer la configuration de monitoring
kubectl apply -f monitoring/
```

---

## 🧹 **Nettoyage**

```bash
# Supprimer tous les ressources
kubectl delete namespace agent-world

# Ou utiliser Kustomize
kubectl delete -k kubernetes/
```

---

## 🔗 **Ressources Utiles**

- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Kustomize Documentation](https://kubectl.docs.kubernetes.io/installation/kustomize/)
- [Helm Documentation](https://helm.sh/docs/)
- [Prometheus Operator](https://prometheus-operator.dev/)

---

## 📝 **Notes**

- Adaptez les configurations (CPU, mémoire, réplicas) en fonction de vos besoins
- Pour la production, utilisez des StorageClasses persistantes
- Configurez des backups réguliers pour Redis et PostgreSQL
- Utilisez des NetworkPolicies pour sécuriser le cluster

---

*Document généré pour le Sprint 6 - Épic 8*
