#!/bin/bash
# Script pour créer les milestones GitHub pour Agent World
# Exécution : bash scripts/create_github_milestones.sh

REPO="GoupilJeremy/agent-world"

echo "🎯 Création des milestones pour $REPO..."

# Fonction pour créer un milestone
create_milestone() {
    local title="$1"
    local description="$2"
    local due_date="$3"
    
    if gh api -X POST /repos/$REPO/milestones \
        -f "title=$title" \
        -f "description=$description" \
        -f "due_on=$due_date" \
        >/dev/null 2>&1; then
        echo "✅ Milestone '$title' créé"
    else
        echo "⚠️  Milestone '$title' existe déjà ou erreur"
    fi
}

# Milestones
create_milestone "MVP" "Épic 1 : Minimum Viable Product - Version v0.1.0" "2026-08-06"
create_milestone "VS Code" "Épic 2 : Intégration VS Code - Version v0.2.0" "2026-08-12"
create_milestone "Files" "Épic 3 : Gestion des Fichiers - Version v0.2.1" "2026-08-19"
create_milestone "History" "Épic 4 : Historique et Versioning - Version v0.3.0" "2026-09-02"
create_milestone "Templates" "Épic 5 : Templates et Personnalisation - Version v0.3.1" "2026-09-16"
create_milestone "Collaboration" "Épic 6 : Collaboration - Version v0.4.0" "2026-09-30"

echo ""
echo "🎉 Tous les milestones ont été créés (ou existent déjà) !"
