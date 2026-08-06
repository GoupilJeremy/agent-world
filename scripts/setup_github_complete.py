#!/usr/bin/env python3
"""
Script Python pour configurer complétement GitHub pour Agent World
Crée les labels, milestones, projet et issues du Sprint 0

Usage:
    python3 scripts/setup_github_complete.py

Le script vous demandera votre token GitHub et exécutera toutes les configurations.
"""

import json
import os
import sys
import time
from typing import List, Dict, Any

# Configuration
REPO = "GoupilJeremy/agent-world"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# Labels à créer (28 labels)
LABELS = [
    # Types
    {"name": "bug", "description": "Bug à corriger", "color": "d73a4a"},
    {"name": "enhancement", "description": "Nouvelle fonctionnalité", "color": "0075ca"},
    {"name": "question", "description": "Question ou demande de clarification", "color": "cc317c"},
    {"name": "documentation", "description": "Mise à jour de la documentation", "color": "0075ca"},
    {"name": "technical-debt", "description": "Tâche technique (refactorisation, etc.)", "color": "f9c514"},
    {"name": "design", "description": "Proposition ou tâche liée au design", "color": "a4a9ad"},
    
    # Priorités
    {"name": "priority: high", "description": "Priorité élevée (P0 - Must Have)", "color": "d73a4a"},
    {"name": "priority: medium", "description": "Priorité moyenne (P1 - Should Have)", "color": "f9c514"},
    {"name": "priority: low", "description": "Priorité basse (P2 - Could Have)", "color": "0e8a16"},
    
    # Épics
    {"name": "epic: mvp", "description": "Épic 1 : MVP", "color": "0075ca"},
    {"name": "epic: vs-code", "description": "Épic 2 : Intégration VS Code", "color": "0075ca"},
    {"name": "epic: files", "description": "Épic 3 : Gestion des Fichiers", "color": "0075ca"},
    {"name": "epic: history", "description": "Épic 4 : Historique et Versioning", "color": "0075ca"},
    {"name": "epic: templates", "description": "Épic 5 : Templates et Personnalisation", "color": "0075ca"},
    {"name": "epic: collaboration", "description": "Épic 6 : Collaboration", "color": "0075ca"},
    {"name": "epic: integrations", "description": "Épic 7 : Intégrations Externes", "color": "0075ca"},
    {"name": "epic: performance", "description": "Épic 8 : Performance et Scalabilité", "color": "0075ca"},
    {"name": "epic: ux", "description": "Épic 9 : Expérience Utilisateur", "color": "0075ca"},
    {"name": "epic: security", "description": "Épic 10 : Sécurité et Conformité", "color": "0075ca"},
    
    # Composants
    {"name": "component: backend", "description": "Backend (Flask/FastAPI)", "color": "0075ca"},
    {"name": "component: frontend", "description": "Frontend (React/Next.js)", "color": "0075ca"},
    {"name": "component: api", "description": "API REST/GraphQL", "color": "0075ca"},
    {"name": "component: cli", "description": "Interface en ligne de commande", "color": "0075ca"},
    {"name": "component: vs-code", "description": "Extension VS Code", "color": "0075ca"},
    {"name": "component: database", "description": "Base de données (PostgreSQL, MongoDB)", "color": "0075ca"},
    {"name": "component: models", "description": "Modèles IA (Mistral, OpenAI, etc.)", "color": "0075ca"},
    
    # Statuts
    {"name": "status: to do", "description": "À faire", "color": "fbca04"},
    {"name": "status: in progress", "description": "En cours", "color": "0075ca"},
    {"name": "status: review", "description": "En revue", "color": "f9c514"},
    {"name": "status: done", "description": "Terminé", "color": "0e8a16"},
    {"name": "status: blocked", "description": "Bloqué", "color": "d73a4a"},
    
    # Pull Requests
    {"name": "pr: needs-review", "description": "Pull Request en attente de revue", "color": "f9c514"},
    {"name": "pr: approved", "description": "Pull Request approuvée", "color": "0e8a16"},
    {"name": "pr: changes-requested", "description": "Pull Request avec des changements demandés", "color": "d73a4a"},
    {"name": "pr: work-in-progress", "description": "Pull Request en cours de développement", "color": "fbca04"},
]

# Milestones à créer (6 milestones)
MILESTONES = [
    {"title": "MVP", "description": "Épic 1 : Minimum Viable Product - Version v0.1.0", "due_on": "2026-08-06"},
    {"title": "VS Code", "description": "Épic 2 : Intégration VS Code - Version v0.2.0", "due_on": "2026-08-12"},
    {"title": "Files", "description": "Épic 3 : Gestion des Fichiers - Version v0.2.1", "due_on": "2026-08-19"},
    {"title": "History", "description": "Épic 4 : Historique et Versioning - Version v0.3.0", "due_on": "2026-09-02"},
    {"title": "Templates", "description": "Épic 5 : Templates et Personnalisation - Version v0.3.1", "due_on": "2026-09-16"},
    {"title": "Collaboration", "description": "Épic 6 : Collaboration - Version v0.4.0", "due_on": "2026-09-30"},
]

# Projet Kanban
PROJECT_NAME = "Agent World Backlog"
PROJECT_DESCRIPTION = "Projet Kanban pour organiser le backlog d'Agent World"
PROJECT_COLUMNS = ["To Do", "In Progress", "Review", "Done", "Blocked"]

# Issues du Sprint 0
SPRINT0_ISSUES = [
    {
        "title": "[FEAT] [VS Code] Ouverture du dashboard VS Code",
        "body": """## 🎯 Description
Créer un dashboard pour visualiser les agents directement depuis VS Code.

---

## ✅ Critères d'Acceptation
- [ ] Extension VS Code créée
- [ ] Affichage des agents dans le dashboard
- [ ] Navigation basique entre les agents

---

## 📌 Détails
- **Épic** : Épic 2 : Intégration VS Code
- **User Story** : US-011
- **Estimation** : 8h
- **Priorité** : P0 (Must Have)""",
        "labels": ["enhancement", "epic: vs-code", "component: vs-code", "priority: high", "status: to do"],
        "milestone": "VS Code"
    },
    {
        "title": "[FEAT] [VS Code] Thème automatique VS Code",
        "body": """## 🎯 Description
Adapter automatiquement le thème de l'extension Agent World au thème VS Code (clair/sombre).

---

## ✅ Critères d'Acceptation
- [ ] Détection automatique du thème VS Code
- [ ] Application du thème clair/sombre
- [ ] Persistance du choix

---

## 📌 Détails
- **Épic** : Épic 2 : Intégration VS Code
- **User Story** : US-012
- **Estimation** : 4h
- **Priorité** : P0 (Must Have)""",
        "labels": ["enhancement", "epic: vs-code", "component: vs-code", "priority: high", "status: to do"],
        "milestone": "VS Code"
    },
    {
        "title": "[FEAT] [VS Code] Ouverture des fichiers dans VS Code",
        "body": """## 🎯 Description
Permettre d'ouvrir les fichiers générés par les agents directement dans VS Code.

---

## ✅ Critères d'Acceptation
- [ ] Commande 'Ouvrir dans VS Code' fonctionnelle
- [ ] Gestion des chemins de fichiers
- [ ] Intégration avec l'explorateur de fichiers

---

## 📌 Détails
- **Épic** : Épic 2 : Intégration VS Code
- **User Story** : US-013
- **Estimation** : 3h
- **Priorité** : P0 (Must Have)""",
        "labels": ["enhancement", "epic: vs-code", "component: vs-code", "priority: high", "status: to do"],
        "milestone": "VS Code"
    },
    {
        "title": "[FEAT] [Files] Dossier de sortie personnalisé",
        "body": """## 🎯 Description
Permettre aux utilisateurs de choisir un dossier de sortie pour les fichiers générés par les agents.

---

## ✅ Critères d'Acceptation
- [ ] Sélection du dossier via l'UI/CLI
- [ ] Persistance du choix
- [ ] Validation du chemin

---

## 📌 Détails
- **Épic** : Épic 3 : Gestion des Fichiers
- **User Story** : US-018
- **Estimation** : 2h
- **Priorité** : P0 (Must Have)""",
        "labels": ["enhancement", "epic: files", "component: backend", "priority: high", "status: to do"],
        "milestone": "Files"
    },
    {
        "title": "[FEAT] [Files] Noms de fichiers intelligents",
        "body": """## 🎯 Description
Générer des noms de fichiers basés sur le contenu (ex: resume_analysis_20260806.md).

---

## ✅ Critères d'Acceptation
- [ ] Algorithme de nommage implémenté
- [ ] Personnalisation possible des noms
- [ ] Support des formats courants (md, txt, json)

---

## 📌 Détails
- **Épic** : Épic 3 : Gestion des Fichiers
- **User Story** : US-019
- **Estimation** : 4h
- **Priorité** : P0 (Must Have)""",
        "labels": ["enhancement", "epic: files", "component: backend", "priority: high", "status: to do"],
        "milestone": "Files"
    }
]


class GitHubSetup:
    """Classe pour gérer la configuration GitHub"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {**HEADERS, "Authorization": f"Bearer {self.token}"}
        self.base_url = f"https://api.github.com/repos/{REPO}"
        self.project_id = None
    
    def api_request(self, method: str, endpoint: str, data: Dict = None) -> Any:
        """Fait une requête à l'API GitHub"""
        import requests
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Méthode {method} non supportée")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"❌ Erreur {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Erreur lors de la requête: {e}")
            return None
    
    def create_labels(self):
        """Crée tous les labels"""
        print("🏷️  Création des labels...")
        
        # Vérifier les labels existants
        existing_labels = self.api_request("GET", "/labels") or []
        existing_label_names = {label["name"] for label in existing_labels}
        
        created_count = 0
        for label in LABELS:
            if label["name"] in existing_label_names:
                print(f"⚠️  Label '{label['name']}' existe déjà")
            else:
                result = self.api_request("POST", "/labels", label)
                if result:
                    print(f"✅ Label '{label['name']}' créé")
                    created_count += 1
                else:
                    print(f"❌ Erreur lors de la création du label '{label['name']}'")
        
        print(f"\n📊 Labels créés: {created_count}/{len(LABELS)}")
        return created_count
    
    def create_milestones(self):
        """Crée tous les milestones"""
        print("\n🎯 Création des milestones...")
        
        # Vérifier les milestones existants
        existing_milestones = self.api_request("GET", "/milestones") or []
        existing_milestone_titles = {m["title"] for m in existing_milestones}
        
        created_count = 0
        for milestone in MILESTONES:
            if milestone["title"] in existing_milestone_titles:
                print(f"⚠️  Milestone '{milestone['title']}' existe déjà")
            else:
                result = self.api_request("POST", "/milestones", milestone)
                if result:
                    print(f"✅ Milestone '{milestone['title']}' créé")
                    created_count += 1
                else:
                    print(f"❌ Erreur lors de la création du milestone '{milestone['title']}'")
        
        print(f"\n📊 Milestones créés: {created_count}/{len(MILESTONES)}")
        return created_count
    
    def create_project(self):
        """Crée le projet Kanban"""
        print("\n📋 Création du projet Kanban...")
        
        # Vérifier si le projet existe déjà
        existing_projects = self.api_request("GET", "/projects") or []
        for project in existing_projects:
            if project["name"] == PROJECT_NAME:
                print(f"⚠️  Projet '{PROJECT_NAME}' existe déjà")
                self.project_id = project["id"]
                return True
        
        # Créer le projet
        project_data = {
            "name": PROJECT_NAME,
            "body": PROJECT_DESCRIPTION
        }
        
        result = self.api_request("POST", "/projects", project_data)
        if result and "id" in result:
            self.project_id = result["id"]
            print(f"✅ Projet '{PROJECT_NAME}' créé avec ID: {self.project_id}")
            
            # Créer les colonnes
            for column_name in PROJECT_COLUMNS:
                column_data = {"name": column_name}
                column_result = self.api_request("POST", f"/projects/{self.project_id}/columns", column_data)
                if column_result:
                    print(f"✅ Colonne '{column_name}' créée")
                else:
                    print(f"⚠️  Colonne '{column_name}' existe déjà ou erreur")
            
            return True
        else:
            print(f"❌ Erreur lors de la création du projet")
            return False
    
    def create_issues(self):
        """Crée toutes les issues du Sprint 0"""
        print("\n📝 Création des issues du Sprint 0...")
        
        created_count = 0
        for issue in SPRINT0_ISSUES:
            # Trouver l'ID du milestone
            milestone_title = issue["milestone"]
            milestones = self.api_request("GET", "/milestones") or []
            milestone_id = None
            for m in milestones:
                if m["title"] == milestone_title:
                    milestone_id = m["id"]
                    break
            
            issue_data = {
                "title": issue["title"],
                "body": issue["body"],
                "labels": issue["labels"]
            }
            
            if milestone_id:
                issue_data["milestone"] = milestone_id
            
            result = self.api_request("POST", "/issues", issue_data)
            if result:
                print(f"✅ Issue '{issue['title']}' créée")
                created_count += 1
            else:
                print(f"❌ Erreur lors de la création de l'issue '{issue['title']}'")
        
        print(f"\n📊 Issues créées: {created_count}/{len(SPRINT0_ISSUES)}")
        return created_count
    
    def verify_setup(self):
        """Vérifie que tout est bien configuré"""
        print("\n🔍 Vérification de la configuration...")
        
        # Vérifier les labels
        labels = self.api_request("GET", "/labels") or []
        print(f"✅ Labels: {len(labels)}/{len(LABELS)} créés")
        
        # Vérifier les milestones
        milestones = self.api_request("GET", "/milestones") or []
        print(f"✅ Milestones: {len(milestones)}/{len(MILESTONES)} créés")
        
        # Vérifier le projet
        projects = self.api_request("GET", "/projects") or []
        project_exists = any(p["name"] == PROJECT_NAME for p in projects)
        print(f"✅ Projet: {'Créé' if project_exists else 'Non créé'}")
        
        # Vérifier les issues
        issues = self.api_request("GET", "/issues?state=all") or []
        print(f"✅ Issues: {len(issues)}/{len(SPRINT0_ISSUES)} créées")


def main():
    """Fonction principale"""
    print("🚀 Configuration GitHub pour Agent World")
    print("=" * 50)
    
    # Demander le token GitHub
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("\n🔐 Veuillez fournir votre Personal Access Token GitHub")
        print("Pour créer un token: https://github.com/settings/tokens")
        print("Permissions requises: repo (full), project (read/write)")
        token = input("\nEntrez votre token GitHub: ").strip()
    
    if not token:
        print("❌ Aucun token fourni. Impossible de continuer.")
        sys.exit(1)
    
    # Créer l'instance
    setup = GitHubSetup(token)
    
    # Exécuter les étapes
    try:
        # 1. Créer les labels
        setup.create_labels()
        
        # 2. Créer les milestones
        setup.create_milestones()
        
        # 3. Créer le projet Kanban
        setup.create_project()
        
        # 4. Créer les issues du Sprint 0
        setup.create_issues()
        
        # 5. Vérification finale
        setup.verify_setup()
        
        print("\n🎉 Configuration GitHub terminée avec succès!")
        print(f"📍 Repository: https://github.com/{REPO}")
        
    except KeyboardInterrupt:
        print("\n❌ Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()