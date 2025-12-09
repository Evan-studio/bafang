#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour supprimer les vidéos des dossiers images/products
Supprime tous les fichiers vidéo (.mp4, .webm, .mov, .avi, .mkv) des dossiers produits
"""

import os
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / 'images' / 'products'

# Extensions vidéo à supprimer
VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.MP4', '.WEBM', '.MOV', '.AVI', '.MKV']

def delete_videos_from_folder(folder_path, dry_run=False):
    """
    Supprime toutes les vidéos d'un dossier.
    
    Args:
        folder_path: Chemin du dossier
        dry_run: Si True, affiche seulement ce qui serait supprimé sans supprimer
    
    Returns:
        Nombre de fichiers supprimés
    """
    if not folder_path.exists() or not folder_path.is_dir():
        return 0
    
    deleted_count = 0
    total_size = 0
    
    for ext in VIDEO_EXTENSIONS:
        videos = list(folder_path.glob(f'*{ext}'))
        for video in videos:
            try:
                file_size = video.stat().st_size
                if dry_run:
                    print(f"  [DRY RUN] Serait supprimé: {video.name} ({file_size / (1024*1024):.2f} MB)")
                else:
                    video.unlink()
                    deleted_count += 1
                    total_size += file_size
                    print(f"  ✅ Supprimé: {video.name} ({file_size / (1024*1024):.2f} MB)")
            except Exception as e:
                print(f"  ❌ Erreur lors de la suppression de {video.name}: {e}")
    
    return deleted_count, total_size

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🗑️  SUPPRESSION DES VIDÉOS DES DOSSIERS IMAGES")
    print("=" * 70)
    print()
    
    if not IMAGES_DIR.exists():
        print(f"❌ Dossier images non trouvé: {IMAGES_DIR}")
        return
    
    print(f"📁 Dossier: {IMAGES_DIR}")
    print()
    
    # Mode dry-run d'abord
    print("🔍 Recherche des vidéos (mode dry-run)...")
    print("-" * 70)
    
    total_videos = 0
    total_size = 0
    folders_with_videos = []
    
    for product_dir in sorted(IMAGES_DIR.iterdir()):
        if not product_dir.is_dir():
            continue
        
        product_id = product_dir.name
        count, size = delete_videos_from_folder(product_dir, dry_run=True)
        
        if count > 0:
            folders_with_videos.append((product_id, count, size))
            total_videos += count
            total_size += size
            print(f"📁 Produit {product_id}: {count} vidéo(s)")
    
    print("-" * 70)
    print(f"📊 Total trouvé: {total_videos} vidéo(s) dans {len(folders_with_videos)} dossier(s)")
    print(f"💾 Taille totale: {total_size / (1024*1024):.2f} MB")
    print()
    
    if total_videos == 0:
        print("ℹ️  Aucune vidéo trouvée. Rien à supprimer.")
        return
    
    # Demander confirmation
    print("⚠️  ATTENTION: Cette opération est irréversible!")
    print()
    response = input(f"Voulez-vous supprimer {total_videos} vidéo(s)? (oui/non): ").strip().lower()
    
    if response not in ('oui', 'o', 'yes', 'y'):
        print("❌ Opération annulée.")
        return
    
    print()
    print("🗑️  Suppression en cours...")
    print("-" * 70)
    
    deleted_count = 0
    deleted_size = 0
    
    for product_id, count, size in folders_with_videos:
        product_dir = IMAGES_DIR / product_id
        print(f"📁 Produit {product_id}:")
        count, size = delete_videos_from_folder(product_dir, dry_run=False)
        deleted_count += count
        deleted_size += size
    
    print("-" * 70)
    print()
    print("=" * 70)
    print("✅ SUPPRESSION TERMINÉE")
    print("=" * 70)
    print(f"📊 Vidéos supprimées: {deleted_count}")
    print(f"💾 Espace libéré: {deleted_size / (1024*1024):.2f} MB")
    print("=" * 70)

if __name__ == '__main__':
    main()


