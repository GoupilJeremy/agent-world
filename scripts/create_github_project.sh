#!/bin/bash
# Script pour créer le projet Kanban GitHub pour Agent World
# Exécution : bash scripts/create_github_project.sh

REPO="GoupilJeremy/agent-world"
PROJECT_NAME="Agent World Backlog"

echo "📋 Création du projet Kanban '$PROJECT_NAME' pour $REPO..."

# Créer le projet (retourne un ID)
PROJECT_ID=$(gh api -X POST /repos/$REPO/projects \
    -f "name=$PROJECT_NAME" \
    -f "body=Projet Kanban pour organiser le backlog d'Agent World" \
    -q '.id' 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "⚠️  Le projet existe déjà ou erreur. Vérifiez manuellement sur GitHub."
    exit 1
fi

echo "✅ Projet '$PROJECT_NAME' créé avec l'ID : $PROJECT_ID"

# Créer les colonnes (To Do, In Progress, Review, Done, Blocked)
COLUMNS=("To Do" "In Progress" "Review" "Done" "Blocked")

for COLUMN in "${COLUMNS[@]}"; do
    if gh api -X POST /projects/$PROJECT_ID/columns \
        -f "name=$COLUMN" \
        >/dev/null 2>&1; then
        echo "✅ Colonne '$COLUMN' créée"
    else
        echo "⚠️  Colonne '$COLUMN' existe déjà ou erreur"
    fi
done

echo ""
echo "🎉 Projet Kanban '$PROJECT_NAME' configuré avec succès !"
echo "🔗 Lien : https://github.com/$REPO/projects/$PROJECT_ID"
