#!/bin/bash

# 🚀 Script pour pousser les fichiers d'Agent World vers GitHub
# Utilisation : ./push-to-github.sh

---

## 📌 Configuration

# Nom du repository GitHub
REPO_NAME="agent-world"
REPO_OWNER="GoupilJeremy"
REPO_URL="git@github.com:${REPO_OWNER}/${REPO_NAME}.git"

# Branche par défaut
BRANCH="main"

---

## 🎯 Fonctions

# Fonction pour afficher un message de succès
success() {
    echo -e "\n✅ $1\n"
}

# Fonction pour afficher un message d'erreur
error() {
    echo -e "\n❌ $1\n"
    exit 1
}

# Fonction pour afficher un message d'information
info() {
    echo -e "\n📌 $1\n"
}

# Fonction pour vérifier si Git est installé
check_git() {
    if ! command -v git &> /dev/null; then
        error "Git n'est pas installé. Veuillez installer Git avant de continuer."
    fi
    success "Git est installé."
}

# Fonction pour vérifier si le repository local existe
check_local_repo() {
    if [ ! -d ".git" ]; then
        error "Le repository local n'existe pas. Veuillez vous placer dans le dossier du repository."
    fi
    success "Repository local trouvé."
}

# Fonction pour vérifier si le repository distant existe
check_remote_repo() {
    if git remote | grep -q "${REPO_OWNER}/${REPO_NAME}"; then
        info "Repository distant déjà configuré : ${REPO_URL}"
    else
        info "Ajout du repository distant : ${REPO_URL}"
        git remote add origin "${REPO_URL}" || error "Impossible d'ajouter le repository distant."
        success "Repository distant ajouté."
    fi
}

# Fonction pour ajouter tous les fichiers
add_files() {
    info "Ajout de tous les fichiers à Git..."
    git add . || error "Impossible d'ajouter les fichiers."
    success "Tous les fichiers ont été ajoutés."
}

# Fonction pour commiter les fichiers
commit_files() {
    info "Commit des fichiers..."
    git commit -m "feat: ajouter backlog complet (60+ user stories, 10 épics)" || error "Impossible de commiter les fichiers."
    success "Commit créé avec succès."
}

# Fonction pour pousser vers GitHub
push_to_github() {
    info "Poussée des fichiers vers GitHub (branche ${BRANCH})..."
    git push -u origin "${BRANCH}" || error "Impossible de pousser les fichiers vers GitHub."
    success "Fichiers poussés vers GitHub avec succès !"
}

# Fonction pour vérifier la poussée
verify_push() {
    info "Vérification de la poussée..."
    git ls-remote --heads origin "${BRANCH}" | grep -q "${BRANCH}" || error "La poussée a échoué."
    success "Poussée vérifiée avec succès."
}

---

## 🚀 Exécution du Script

# Afficher le titre
clear
echo ""
echo "┌───────────────────────────────────────────────────────────────────────────────┐"
echo "│                    Poussée des fichiers vers GitHub                            │"
echo "│                         Agent World                                           │"
echo "└───────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Vérifier Git
check_git

# Vérifier le repository local
check_local_repo

# Vérifier le repository distant
check_remote_repo

# Ajouter les fichiers
add_files

# Commiter les fichiers
commit_files

# Pousser vers GitHub
push_to_github

# Vérifier la poussée
verify_push

---

## 🎉 Fin du Script

echo ""
echo "┌───────────────────────────────────────────────────────────────────────────────┐"
echo "│                    ✅ Poussée terminée avec succès !                              │"
echo "│                                                                               │"
echo "│  Repository : https://github.com/${REPO_OWNER}/${REPO_NAME}                   │"
echo "│  Branche : ${BRANCH}                                                                   │"
echo "│                                                                               │"
echo "│  Prochaines étapes :                                                             │"
echo "│  1. Configurer les labels GitHub (voir .github/PROJECT.md)                    │"
echo "│  2. Configurer les milestones (voir .github/PROJECT.md)                      │"
echo "│  3. Créer les issues du Sprint 0 (voir BACKLOG.md)                            │"
echo "│  4. Configurer GitHub Projects (voir .github/PROJECT.md)                     │"
echo "│  5. Configurer la CI/CD (voir .github/PROJECT.md)                            │"
echo "│                                                                               │"
echo "└───────────────────────────────────────────────────────────────────────────────┘"
echo ""
