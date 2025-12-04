#!/usr/bin/env python3
"""
Script maître pour générer tout le site en Allemand dans le dossier de.

Ce script lance tous les scripts de génération dans le bon ordre :
1. update_index_template.py - Génère l'index.html
2. generate_and_check_menu_footer_pages.py - Génère les pages catégories et légales
3. generate_all_product_pages.py - Génère toutes les pages produits
"""

import subprocess
import sys
from pathlib import Path

LANG_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = LANG_DIR / 'scripts' / 'generate'

def run_script(script_name):
    """Lance un script Python."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"❌ Script non trouvé: {script_path}")
        return False
    
    print(f"\n{'='*70}")
    print(f"🚀 Lancement de {script_name}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(LANG_DIR),
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        print(f"\n✅ {script_name} terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de l'exécution de {script_name}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        print(f"Code de retour: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        return False

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🌍 GÉNÉRATION COMPLÈTE DU SITE")
    print("=" * 70)
    print(f"\n📁 Dossier de travail: {LANG_DIR}")
    
    scripts = [
        'update_index_template.py',
        'generate_and_check_menu_footer_pages.py',
        'generate_all_product_pages.py'
    ]
    
    success = True
    for script in scripts:
        if not run_script(script):
            success = False
            print(f"\n⚠️  Arrêt après l'erreur dans {script}")
            break
    
    print("\n" + "=" * 70)
    if success:
        print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
    else:
        print("❌ GÉNÉRATION TERMINÉE AVEC DES ERREURS")
    print("=" * 70)

if __name__ == '__main__':
    main()
