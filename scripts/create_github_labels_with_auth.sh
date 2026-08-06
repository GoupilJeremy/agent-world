#!/bin/bash
# Script pour créer les labels GitHub pour Agent World avec authentification
# Usage: GITHUB_TOKEN=ton_token bash scripts/create_github_labels_with_auth.sh

REPO="GoupilJeremy/agent-world"
GH_CLI="/tmp/vibe-scratchpad-6333f312-hy2ab97o/gh"

# Vérifier si on a un token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Veuillez fournir un token GitHub via la variable GITHUB_TOKEN"
    echo "Exemple: GITHUB_TOKEN=votre_token bash $0"
    exit 1
fi

# Configurer gh avec le token
export GH_TOKEN="$GITHUB_TOKEN"

echo "🏷️  Création des labels pour $REPO..."

# Fonction pour créer un label
create_label() {
    local name="$1"
    local description="$2"
    local color="$3"
    
    if $GH_CLI api -X POST /repos/$REPO/labels -f "name=$name" -f "description=$description" -f "color=$color" >/dev/null 2>&1; then
        echo "✅ Label '$name' créé"
    else
        echo "⚠️  Label '$name' existe déjà ou erreur"
    fi
}

# Labels par Type
create_label "bug" "Bug à corriger" "d73a4a"
create_label "enhancement" "Nouvelle fonctionnalité" "0075ca"
create_label "question" "Question ou demande de clarification" "cc317c"
create_label "documentation" "Mise à jour de la documentation" "0075ca"
create_label "technical-debt" "Tâche technique (refactorisation, etc.)" "f9c514"
create_label "design" "Proposition ou tâche liée au design" "a4a9ad"

# Labels par Priorité
create_label "priority: high" "Priorité élevée (P0 - Must Have)" "d73a4a"
create_label "priority: medium" "Priorité moyenne (P1 - Should Have)" "f9c514"
create_label "priority: low" "Priorité basse (P2 - Could Have)" "0e8a16"

# Labels par Épic
create_label "epic: mvp" "Épic 1 : MVP" "0075ca"
create_label "epic: vs-code" "Épic 2 : Intégration VS Code" "0075ca"
create_label "epic: files" "Épic 3 : Gestion des Fichiers" "0075ca"
create_label "epic: history" "Épic 4 : Historique et Versioning" "0075ca"
create_label "epic: templates" "Épic 5 : Templates et Personnalisation" "0075ca"
create_label "epic: collaboration" "Épic 6 : Collaboration" "0075ca"
create_label "epic: integrations" "Épic 7 : Intégrations Externes" "0075ca"
create_label "epic: performance" "Épic 8 : Performance et Scalabilité" "0075ca"
create_label "epic: ux" "Épic 9 : Expérience Utilisateur" "0075ca"
create_label "epic: security" "Épic 10 : Sécurité et Conformité" "0075ca"

# Labels par Composant
create_label "component: backend" "Backend (Flask/FastAPI)" "0075ca"
create_label "component: frontend" "Frontend (React/Next.js)" "0075ca"
create_label "component: api" "API REST/GraphQL" "0075ca"
create_label "component: cli" "Interface en ligne de commande" "0075ca"
create_label "component: vs-code" "Extension VS Code" "0075ca"
create_label "component: database" "Base de données (PostgreSQL, MongoDB)" "0075ca"
create_label "component: models" "Modèles IA (Mistral, OpenAI, etc.)" "0075ca"

# Labels par Statut
create_label "status: to do" "À faire" "fbca04"
create_label "status: in progress" "En cours" "0075ca"
create_label "status: review" "En revue" "f9c514"
create_label "status: done" "Terminé" "0e8a16"
create_label "status: blocked" "Bloqué" "d73a4a"

# Labels pour les Pull Requests
create_label "pr: needs-review" "Pull Request en attente de revue" "f9c514"
create_label "pr: approved" "Pull Request approuvée" "0e8a16"
create_label "pr: changes-requested" "Pull Request avec des changements demandés" "d73a4a"
create_label "pr: work-in-progress" "Pull Request en cours de développement" "fbca04"

echo ""
echo "🎉 Tous les labels ont été créés (ou existent déjà) !"

# Vérification
$GH_CLI api /repos/$REPO/labels | python3 -c "import sys, json; labels = json.load(sys.stdin); print(f'Nombre total de labels: {len(labels)}')"