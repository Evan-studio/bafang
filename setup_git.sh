#!/bin/bash
# Script pour initialiser Git et connecter au dépôt GitHub

echo "🚀 Configuration Git pour le projet Makita"
echo ""

# Aller dans le dossier
cd "/Users/terrybauer/Documents/site affiliation/Makita"

# Initialiser Git
echo "📦 Initialisation de Git..."
git init

# Ajouter tous les fichiers
echo "➕ Ajout des fichiers..."
git add .

# Premier commit
echo "💾 Premier commit..."
git commit -m "Initial commit - Site Makita multilingue"

# Ajouter le dépôt distant
echo "🔗 Connexion au dépôt GitHub..."
git remote add origin https://github.com/Evan-studio/makita.git

# Renommer la branche principale
echo "🌿 Configuration de la branche main..."
git branch -M main

echo ""
echo "✅ Configuration terminée !"
echo ""
echo "📤 Pour pousser votre code sur GitHub, exécutez :"
echo "   git push -u origin main"
echo ""



