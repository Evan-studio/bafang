#!/usr/bin/env python3
"""
Script master pour régénérer TOUT le site dans toutes les langues
ET mettre à jour les domaines automatiquement.

Ce script exécute dans l'ordre pour chaque langue :
1. update_index_template.py - Met à jour index.html
2. generate_and_check_menu_footer_pages.py - Génère les pages catégories et légales
3. generate_all_product_pages.py - Génère toutes les pages produits
4. update_domain_urls.py - Met à jour toutes les URLs avec le domaine du CSV

Usage:
    python3 generate_all_languages_with_domain_update.py
"""

import csv
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

def detect_languages():
    """Détecte automatiquement toutes les langues disponibles."""
    languages = []
    
    # Langue principale (en) - dossier racine
    if (BASE_DIR / 'index.html').exists() and (BASE_DIR / 'translations.csv').exists():
        languages.append({
            'code': 'en',
            'name': 'Anglais',
            'generate_script': BASE_DIR / 'generate_all_en.py',
            'update_script': BASE_DIR / 'scripts' / 'generate' / 'update_domain_urls.py',
            'dir': BASE_DIR
        })
    
    # Autres langues - dossiers avec index.html et translations.csv
    for lang_dir in BASE_DIR.iterdir():
        if lang_dir.is_dir() and not lang_dir.name.startswith('.') and lang_dir.name not in ['scripts', 'CSV', 'upload youtube', 'page_html']:
            index_file = lang_dir / 'index.html'
            translations_file = lang_dir / 'translations.csv'
            
            if index_file.exists() and translations_file.exists():
                lang_code = lang_dir.name
                # Nom de la langue depuis translations.csv ou utiliser le code
                lang_name = lang_code.upper()
                try:
                    import pandas as pd
                    df = pd.read_csv(translations_file, nrows=1)
                    if 'langue' in df.columns:
                        lang_name = df['langue'].iloc[0] if pd.notna(df['langue'].iloc[0]) else lang_code.upper()
                except:
                    pass
                
                generate_script = lang_dir / 'scripts' / f'generate_all_{lang_code}.py'
                update_script = lang_dir / 'scripts' / 'generate' / 'update_domain_urls.py'
                
                languages.append({
                    'code': lang_code,
                    'name': lang_name,
                    'generate_script': generate_script,
                    'update_script': update_script,
                    'dir': lang_dir
                })
    
    return languages

LANGUAGES = detect_languages()


def propagate_youtube_urls_from_root():
    """
    Copie les youtube_url depuis CSV/all_products.csv (racine)
    vers chaque CSV de langue si la valeur est manquante.
    """
    root_csv = BASE_DIR / 'CSV' / 'all_products.csv'
    if not root_csv.exists():
        print("⚠️  CSV racine introuvable, propagation youtube ignorée")
        return

    # Construire un mapping product_id -> youtube_url (non vide) depuis le CSV racine
    root_youtube_map = {}
    try:
        with open(root_csv, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = (row.get('product_id') or '').strip()
                yt = (row.get('youtube_url') or '').strip()
                if pid and yt:
                    root_youtube_map[pid] = yt
    except Exception as e:
        print(f"⚠️  Impossible de lire le CSV racine pour les youtube_url : {e}")
        return

    if not root_youtube_map:
        print("ℹ️  Aucun youtube_url détecté dans le CSV racine, rien à propager")
        return

    print(f"🔄 Propagation des youtube_url vers {len(LANGUAGES)} langues...")

    for lang in LANGUAGES:
        # Le dossier racine (en) utilise déjà root_csv
        if lang['code'] == 'en':
            continue

        lang_csv = lang['dir'] / 'CSV' / 'all_products.csv'
        if not lang_csv.exists():
            print(f"  ⚠️  CSV manquant pour {lang['code']}: {lang_csv}")
            continue

        try:
            with open(lang_csv, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames or []

            # S'assurer que la colonne existe
            if 'youtube_url' not in fieldnames:
                fieldnames = fieldnames + ['youtube_url']

            updated = False
            for row in rows:
                pid = (row.get('product_id') or '').strip()
                if not pid:
                    continue
                yt_root = root_youtube_map.get(pid, '')
                yt_lang = (row.get('youtube_url') or '').strip()
                if yt_root and not yt_lang:
                    row['youtube_url'] = yt_root
                    updated = True

            if updated:
                with open(lang_csv, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                print(f"  ✅ youtube_url propagées pour {lang['code']}")
            else:
                print(f"  ℹ️  Rien à mettre à jour pour {lang['code']}")

        except Exception as e:
            print(f"  ❌ Erreur propagation youtube pour {lang['code']}: {e}")

def run_script(script_path, lang_name, step_name):
    """Exécute un script."""
    if not script_path.exists():
        print(f"  ⚠️  Script non trouvé: {script_path}")
        return False
    
    try:
        print(f"  📄 {step_name}...")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=script_path.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✅ {step_name} - Terminé")
            return True
        else:
            print(f"  ❌ {step_name} - Erreur:")
            if result.stderr:
                print(result.stderr[:500])  # Limiter l'affichage
            return False
    except Exception as e:
        print(f"  ❌ {step_name} - Exception: {e}")
        return False

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🌍 RÉGÉNÉRATION COMPLÈTE + MISE À JOUR DES DOMAINES")
    print("=" * 70)
    print()

    # Propager les youtube_url vers les CSV de chaque langue avant génération
    propagate_youtube_urls_from_root()
    
    success_count = 0
    total_count = len(LANGUAGES)
    
    for lang in LANGUAGES:
        print(f"\n{'=' * 70}")
        print(f"🌐 {lang['name'].upper()} ({lang['code']})")
        print(f"{'=' * 70}")
        
        # Étape 1: Génération
        if not run_script(lang['generate_script'], lang['name'], "Génération"):
            print(f"  ⚠️  Échec de la génération pour {lang['name']}")
            continue
        
        # Étape 2: Mise à jour des domaines
        if not run_script(lang['update_script'], lang['name'], "Mise à jour des domaines"):
            print(f"  ⚠️  Échec de la mise à jour des domaines pour {lang['name']}")
            continue
        
        success_count += 1
    
    print()
    print("=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print(f"✅ Réussi: {success_count}/{total_count}")
    print(f"❌ Échoué: {total_count - success_count}/{total_count}")
    print()
    
    if success_count == total_count:
        print("🎉 Toutes les langues ont été régénérées avec succès !")
        print()
        print("📝 Prochaines étapes:")
        print("  1. Régénérer les sitemaps: python3 generate_sitemaps.py")
        print("  2. Vérifier les fichiers générés")
        print("  3. Déployer: python3 update_github_auto.py")
    else:
        print("⚠️  Certaines langues ont échoué. Vérifiez les erreurs ci-dessus.")
        sys.exit(1)

if __name__ == '__main__':
    main()

