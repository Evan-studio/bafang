#!/usr/bin/env python3
"""
Script pour copier le site depuis Desktop vers le dossier Makita
"""
import shutil
from pathlib import Path

source = Path("/Users/terrybauer/Desktop/site affiliation-test 3:11:25 copie")
destination = Path("/Users/terrybauer/Documents/site affiliation/Makita")

# Exclure certains dossiers/fichiers
exclude_patterns = [
    '__pycache__',
    '*.pyc',
    '.DS_Store',
    '.git',
]

print(f"📁 Copie de {source} vers {destination}...")

# Copier le contenu
if source.exists():
    # Copier tous les fichiers et dossiers
    for item in source.iterdir():
        if item.name == '.git':
            continue
        dest_item = destination / item.name
        print(f"  📋 Copie: {item.name}")
        if item.is_dir():
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest_item)
    
    print(f"\n✅ Copie terminée !")
    print(f"📁 Destination: {destination}")
else:
    print(f"❌ Source introuvable: {source}")



