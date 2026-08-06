#!/bin/bash
# Script pour créer les issues du Sprint 0 pour Agent World
# Exécution : bash scripts/create_sprint0_issues.sh

REPO="GoupilJeremy/agent-world"
MILESTONE_VS_CODE="VS Code"
MILESTONE_FILES="Files"

echo "📝 Création des issues du Sprint 0 pour $REPO..."

# Fonction pour créer une issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"
    local milestone="$4"
    
    if gh api -X POST /repos/$REPO/issues \
        -f "title=$title" \
        -f "body=$body" \
        -f "labels=$labels" \
        -f "milestone=$milestone" \
        >/dev/null 2>&1; then
        echo "✅ Issue '$title' créée"
    else
        echo "⚠️  Issue '$title' existe déjà ou erreur"
    fi
}

# US-011 : Ouverture du dashboard VS Code
create_issue \
    "[FEAT] [VS Code] Ouverture du dashboard VS Code" \
    "## 🎯 Description
Créer un dashboard pour visualiser les agents directement depuis VS Code.

---

## ✅ Critères d'Acceptation
- [ ] Extension VS Code créée
- [ ] Affichage des agents dans le dashboard
- [ ] Navigation basique entre les agents

---

## 📌 Détails
- **Épic** : [Épic 2 : Intégration VS Code](BACKLOG.md#épic-2--intégration-vs-code)
- **User Story** : US-011
- **Estimation** : 8h
- **Priorité** : P0 (Must Have)" \
    "enhancement,epic: vs-code,component: vs-code,priority: high,status: to do" \
    "$MILESTONE_VS_CODE"

# US-012 : Thème automatique VS Code
create_issue \
    "[FEAT] [VS Code] Thème automatique VS Code" \
    "## 🎯 Description
Adapter automatiquement le thème de l'extension Agent World au thème VS Code (clair/sombre).

---

## ✅ Critères d'Acceptation
- [ ] Détection automatique du thème VS Code
- [ ] Application du thème clair/sombre
- [ ] Persistance du choix

---

## 📌 Détails
- **Épic** : [Épic 2 : Intégration VS Code](BACKLOG.md#épic-2--intégration-vs-code)
- **User Story** : US-012
- **Estimation** : 4h
- **Priorité** : P0 (Must Have)" \
    "enhancement,epic: vs-code,component: vs-code,priority: high,status: to do" \
    "$MILESTONE_VS_CODE"

# US-013 : Ouverture des fichiers dans VS Code
create_issue \
    "[FEAT] [VS Code] Ouverture des fichiers dans VS Code" \
    "## 🎯 Description
Permettre d'ouvrir les fichiers générés par les agents directement dans VS Code.

---

## ✅ Critères d'Acceptation
- [ ] Commande 'Ouvrir dans VS Code' fonctionnelle
- [ ] Gestion des chemins de fichiers
- [ ] Intégration avec l'explorateur de fichiers

---

## 📌 Détails
- **Épic** : [Épic 2 : Intégration VS Code](BACKLOG.md#épic-2--intégration-vs-code)
- **User Story** : US-013
- **Estimation** : 3h
- **Priorité** : P0 (Must Have)" \
    "enhancement,epic: vs-code,component: vs-code,priority: high,status: to do" \
    "$MILESTONE_VS_CODE"

# US-018 : Dossier de sortie personnalisé
create_issue \
    "[FEAT] [Files] Dossier de sortie personnalisé" \
    "## 🎯 Description
Permettre aux utilisateurs de choisir un dossier de sortie pour les fichiers générés par les agents.

---

## ✅ Critères d'Acceptation
- [ ] Sélection du dossier via l'UI/CLI
- [ ] Persistance du choix
- [ ] Validation du chemin

---

## 📌 Détails
- **Épic** : [Épic 3 : Gestion des Fichiers](BACKLOG.md#épic-3--gestion-des-fichiers)
- **User Story** : US-018
- **Estimation** : 2h
- **Priorité** : P0 (Must Have)" \
    "enhancement,epic: files,component: backend,priority: high,status: to do" \
    "$MILESTONE_FILES"

# US-019 : Noms de fichiers intelligents
create_issue \
    "[FEAT] [Files] Noms de fichiers intelligents" \
    "## 🎯 Description
Générer des noms de fichiers basés sur le contenu (ex: `resume_analysis_20260806.md`).

---

## ✅ Critères d'Acceptation
- [ ] Algorithme de nommage implémenté
- [ ] Personnalisation possible des noms
- [ ] Support des formats courants (md, txt, json)

---

## 📌 Détails
- **Épic** : [Épic 3 : Gestion des Fichiers](BACKLOG.md#épic-3--gestion-des-fichiers)
- **User Story** : US-019
- **Estimation** : 4h
- **Priorité** : P0 (Must Have)" \
    "enhancement,epic: files,component: backend,priority: high,status: to do" \
    "$MILESTONE_FILES"

echo ""
echo "🎉 Toutes les issues du Sprint 0 ont été créées (ou existent déjà) !"
