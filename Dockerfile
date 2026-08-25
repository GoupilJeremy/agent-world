# 🐳 Agent World - Dockerfile
# Version: 0.1.0 (MVP)
# Description: Configuration Docker pour le backend

# Utiliser une image Python officielle
FROM python:3.11-slim as builder

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --user -r requirements.txt

# Créer une image finale plus légère
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances installées depuis le stage builder
COPY --from=builder /root/.local /root/.local

# Ajouter le répertoire .local au PATH
ENV PATH=/root/.local/bin:$PATH

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/outputs /app/logs /app/data

# Définir les variables d'environnement
ENV FLASK_APP=run:app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Exposer le port de l'application
EXPOSE 5000

# Appliquer les migrations avant de lancer le serveur de production.
CMD ["sh", "-c", "alembic upgrade head && python run.py --production"]
