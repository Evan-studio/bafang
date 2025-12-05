#!/usr/bin/env python3
"""
Script pour initialiser Git et connecter au dépôt GitHub
"""
import subprocess
import os
from pathlib import Path

# Aller dans le dossier
os.chdir("/Users/terrybauer/Documents/site affiliation/Makita")

print("🚀 Configuration Git pour le projet Makita")
print("=" * 60)
print()

# 1. Initialiser Git
print("📦 1. Initialisation de Git...")
try:
    subprocess.run(["git", "init"], check=True, capture_output=True)
    print("   ✅ Git initialisé")
except subprocess.CalledProcessError as e:
    print(f"   ⚠️  Erreur: {e}")
    if "already a git repository" in str(e.stderr):
        print("   ℹ️  Git déjà initialisé, on continue...")
print()

# 2. Ajouter tous les fichiers
print("➕ 2. Ajout des fichiers...")
try:
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    print("   ✅ Fichiers ajoutés")
except subprocess.CalledProcessError as e:
    print(f"   ❌ Erreur: {e}")
print()

# 3. Vérifier si remote existe déjà
print("🔍 3. Vérification du dépôt distant...")
result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
if "origin" in result.stdout:
    print("   ℹ️  Remote 'origin' existe déjà")
    print("   🔄 Suppression de l'ancien remote...")
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
print()

# 4. Ajouter le dépôt distant
print("🔗 4. Connexion au dépôt GitHub...")
try:
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/Evan-studio/makita.git"],
        check=True,
        capture_output=True
    )
    print("   ✅ Dépôt GitHub connecté")
except subprocess.CalledProcessError as e:
    if "already exists" in str(e.stderr):
        print("   ℹ️  Remote existe déjà")
    else:
        print(f"   ❌ Erreur: {e}")
print()

# 5. Premier commit
print("💾 5. Création du premier commit...")
try:
    result = subprocess.run(
        ["git", "commit", "-m", "Initial commit - Site Makita multilingue"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("   ✅ Commit créé")
    elif "nothing to commit" in result.stdout:
        print("   ℹ️  Rien à committer (déjà commité)")
    else:
        print(f"   ⚠️  {result.stdout}")
except subprocess.CalledProcessError as e:
    print(f"   ⚠️  Erreur: {e}")
print()

# 6. Renommer la branche principale
print("🌿 6. Configuration de la branche main...")
try:
    subprocess.run(["git", "branch", "-M", "main"], check=True, capture_output=True)
    print("   ✅ Branche 'main' configurée")
except subprocess.CalledProcessError as e:
    print(f"   ⚠️  Erreur: {e}")
print()

print("=" * 60)
print("✅ Configuration Git terminée !")
print()
print("📤 Prochaine étape : Pousser sur GitHub")
print("   Exécutez cette commande dans Terminal :")
print("   cd '/Users/terrybauer/Documents/site affiliation/Makita'")
print("   git push -u origin main")
print()



