#!/usr/bin/env python3
"""
Script master pour régénérer tout le site en anglais (racine).

Ce script exécute dans l'ordre :
1. update_index_template.py - Met à jour index.html
2. generate_and_check_menu_footer_pages.py - Génère les pages catégories et légales
3. generate_all_product_pages.py - Génère toutes les pages produits

Usage:
    python3 generate_all_en.py
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / 'scripts' / 'generate'

scripts = [
    'update_index_template.py',
    'generate_and_check_menu_footer_pages.py',
    'generate_all_product_pages.py'
]

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🚀 RÉGÉNÉRATION DU SITE EN ANGLAIS (RACINE)")
    print("=" * 70)
    print()
    
    for i, script in enumerate(scripts, 1):
        script_path = SCRIPTS_DIR / script
        if not script_path.exists():
            print(f"❌ Script non trouvé: {script_path}")
            return False
        
        print(f"📄 [{i}/{len(scripts)}] Exécution de {script}...")
        print("-" * 70)
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=BASE_DIR,
                check=True
            )
            print(f"✅ {script} terminé avec succès")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'exécution de {script}")
            print(f"   Code de retour: {e.returncode}")
            return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
        
        print()
    
    print("=" * 70)
    print("✅ SITE EN ANGLAIS RÉGÉNÉRÉ AVEC SUCCÈS!")
    print("=" * 70)
    print()
    print("💡 Prochaines étapes:")
    print("   1. Vérifiez que les pages sont correctement générées")
    print("   2. Régénérez les sitemaps: python3 generate_sitemaps.py")
    print("   3. Commit et push sur GitHub pour déployer")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



