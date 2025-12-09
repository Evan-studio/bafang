#!/usr/bin/env python3
"""
Script pour générer automatiquement les sitemaps pour tous les sites multilingues.

Ce script :
1. Détecte automatiquement tous les dossiers de langue (fr/, de/, es/, etc.)
2. Génère un sitemap spécifique pour chaque langue avec les bonnes URLs
3. Génère un sitemap index à la racine qui référence tous les sitemaps de langue
4. Met à jour automatiquement quand on ajoute une nouvelle langue

Usage:
    python3 generate_sitemaps.py
"""

import csv
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent

# Dossiers à exclure lors de la détection des langues
EXCLUDED_DIRS = {
    'APPLI:SCRIPT aliexpress', 'scripts', 'config', 'images', 'page_html', 
    'upload_cloudflare', 'sauv', 'CSV', '__pycache__', '.git', 'node_modules'
}

def find_language_directories():
    """Trouve automatiquement tous les dossiers de langue."""
    lang_dirs = []
    for item in BASE_DIR.iterdir():
        if (item.is_dir() and 
            not item.name.startswith('.') and 
            item.name not in EXCLUDED_DIRS and
            (item / 'index.html').exists() and 
            (item / 'translations.csv').exists()):
            lang_dirs.append(item)
    return sorted(lang_dirs, key=lambda x: x.name.lower())

def load_domain_from_csv(lang_dir):
    """Charge le domaine depuis translations.csv d'une langue."""
    translations_csv = lang_dir / 'translations.csv'
    if not translations_csv.exists():
        return None
    
    try:
        with open(translations_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get('key', '').strip()
                if key == 'site.domain':
                    # Chercher dans toutes les colonnes possibles
                    domain = None
                    for col in row.keys():
                        if col != 'key' and col != 'description':
                            value = row.get(col, '').strip()
                            if value and not value.startswith('=') and not value.startswith('#'):
                                domain = value
                                break
                    
                    if domain:
                        # Nettoyer le domaine
                        domain = domain.rstrip('/')
                        if not domain.startswith('http'):
                            domain = f'https://{domain}'
                        return domain
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la lecture du CSV: {e}")
    
    return None

def get_base_domain():
    """Trouve le domaine de base en cherchant dans tous les dossiers de langue."""
    lang_dirs = find_language_directories()
    for lang_dir in lang_dirs:
        domain = load_domain_from_csv(lang_dir)
        if domain:
            return domain
    
    # Fallback : chercher dans translations.csv à la racine
    root_translations = BASE_DIR / 'translations.csv'
    if root_translations.exists():
        try:
            with open(root_translations, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = row.get('key', '').strip()
                    if key == 'site.domain':
                        for col in row.keys():
                            if col != 'key' and col != 'description':
                                value = row.get(col, '').strip()
                                if value and not value.startswith('=') and not value.startswith('#'):
                                    domain = value.rstrip('/')
                                    if not domain.startswith('http'):
                                        domain = f'https://{domain}'
                                    return domain
        except:
            pass
    
    # Fallback par défaut
    return 'https://www.senseofthailand.com'

def get_lastmod_date(file_path):
    """Récupère la date de modification d'un fichier."""
    if file_path.exists():
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    return datetime.now().strftime('%Y-%m-%d')

def find_html_pages(lang_dir, lang_code):
    """Trouve toutes les pages HTML d'une langue."""
    pages = []
    base_domain = get_base_domain()
    
    # Index de la langue
    index_file = lang_dir / 'index.html'
    if index_file.exists():
        pages.append({
            'url': f'{base_domain}/{lang_code}/',
            'lastmod': get_lastmod_date(index_file),
            'priority': '1.0',
            'changefreq': 'daily'
        })
    
    # Pages catégories (sans extension .html car Cloudflare Pages les sert sans)
    categories_dir = lang_dir / 'page_html' / 'categories'
    if categories_dir.exists():
        for html_file in sorted(categories_dir.glob('*.html')):
            if html_file.name != 'index.html':  # Exclure les index.html dans les catégories
                # Enlever l'extension .html pour l'URL
                url_name = html_file.stem
                pages.append({
                    'url': f'{base_domain}/{lang_code}/page_html/categories/{url_name}',
                    'lastmod': get_lastmod_date(html_file),
                    'priority': '0.8',
                    'changefreq': 'weekly'
                })
    
    # Pages produits (sans extension .html)
    products_dir = lang_dir / 'page_html' / 'products'
    if products_dir.exists():
        for html_file in sorted(products_dir.glob('produit-*.html')):
            # Enlever l'extension .html pour l'URL
            url_name = html_file.stem
            pages.append({
                'url': f'{base_domain}/{lang_code}/page_html/products/{url_name}',
                'lastmod': get_lastmod_date(html_file),
                'priority': '0.7',
                'changefreq': 'monthly'
            })
    
    # Pages légales (sans extension .html)
    legal_dir = lang_dir / 'page_html' / 'legal'
    if legal_dir.exists():
        for html_file in sorted(legal_dir.glob('*.html')):
            # Enlever l'extension .html pour l'URL
            url_name = html_file.stem
            pages.append({
                'url': f'{base_domain}/{lang_code}/page_html/legal/{url_name}',
                'lastmod': get_lastmod_date(html_file),
                'priority': '0.5',
                'changefreq': 'monthly'
            })
    
    return pages

def generate_language_sitemap(lang_dir, lang_code):
    """Génère un sitemap XML pour une langue spécifique."""
    pages = find_html_pages(lang_dir, lang_code)
    
    if not pages:
        print(f"  ⚠️  Aucune page trouvée pour {lang_code}")
        return None
    
    sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for page in pages:
        sitemap_content.append('  <url>')
        sitemap_content.append(f'    <loc>{page["url"]}</loc>')
        sitemap_content.append(f'    <lastmod>{page["lastmod"]}</lastmod>')
        sitemap_content.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
        sitemap_content.append(f'    <priority>{page["priority"]}</priority>')
        sitemap_content.append('  </url>')
    
    sitemap_content.append('</urlset>')
    
    return '\n'.join(sitemap_content)

def generate_sitemap_index(lang_codes):
    """Génère le sitemap index qui référence tous les sitemaps de langue."""
    base_domain = get_base_domain()
    today = datetime.now().strftime('%Y-%m-%d')
    
    sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_content.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # Trier les codes de langue pour avoir 'en' en premier
    sorted_lang_codes = sorted(lang_codes, key=lambda x: (x != 'en', x))
    
    for lang_code in sorted_lang_codes:
        sitemap_url = f'{base_domain}/sitemap-{lang_code}.xml'
        sitemap_content.append('  <sitemap>')
        sitemap_content.append(f'    <loc>{sitemap_url}</loc>')
        sitemap_content.append(f'    <lastmod>{today}</lastmod>')
        sitemap_content.append('  </sitemap>')
    
    sitemap_content.append('</sitemapindex>')
    
    return '\n'.join(sitemap_content)

def cleanup_old_sitemaps():
    """Supprime tous les anciens fichiers sitemap avant de générer les nouveaux."""
    deleted_count = 0
    
    # Supprimer les sitemaps à la racine
    for sitemap_file in BASE_DIR.glob('sitemap*.xml'):
        try:
            sitemap_file.unlink()
            deleted_count += 1
            print(f"  🗑️  Supprimé: {sitemap_file.name}")
        except Exception as e:
            print(f"  ⚠️  Erreur lors de la suppression de {sitemap_file.name}: {e}")
    
    # Supprimer les sitemaps dans les dossiers de langue
    for item in BASE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name not in EXCLUDED_DIRS:
            for sitemap_file in item.glob('sitemap*.xml'):
                try:
                    sitemap_file.unlink()
                    deleted_count += 1
                    print(f"  🗑️  Supprimé: {item.name}/{sitemap_file.name}")
                except Exception as e:
                    print(f"  ⚠️  Erreur lors de la suppression de {item.name}/{sitemap_file.name}: {e}")
    
    return deleted_count

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🗺️  GÉNÉRATION DES SITEMAPS MULTILINGUES")
    print("=" * 70)
    print()
    
    # 0. Nettoyer les anciens sitemaps
    print("🧹 Nettoyage des anciens sitemaps...")
    deleted_count = cleanup_old_sitemaps()
    if deleted_count > 0:
        print(f"  ✅ {deleted_count} ancien(s) sitemap(s) supprimé(s)")
    else:
        print("  ℹ️  Aucun ancien sitemap trouvé")
    print()
    
    # 1. Détecter tous les dossiers de langue
    print("🔍 Détection des sites de langue...")
    lang_dirs = find_language_directories()
    
    if not lang_dirs:
        print("❌ Aucun dossier de langue trouvé")
        print("   Assurez-vous que chaque langue a un dossier avec index.html et translations.csv")
        return False
    
    print(f"✅ {len(lang_dirs)} site(s) de langue détecté(s):")
    for lang_dir in lang_dirs:
        print(f"   - {lang_dir.name}/")
    print()
    
    # 2. Récupérer le domaine
    base_domain = get_base_domain()
    print(f"🌐 Domaine détecté: {base_domain}")
    print()
    
    # 3. Générer un sitemap pour la racine (en) si elle existe
    generated_sitemaps = []
    root_index = BASE_DIR / 'index.html'
    root_translations = BASE_DIR / 'translations.csv'
    
    if root_index.exists() and root_translations.exists():
        print("📝 Génération des sitemaps par langue...")
        print("-" * 70)
        print(f"\n📄 Génération de sitemap-en.xml (racine)...")
        
        # Générer le sitemap pour la racine (en)
        root_pages = []
        base_domain = get_base_domain()
        
        # Index de la racine
        root_pages.append({
            'url': f'{base_domain}/',
            'lastmod': get_lastmod_date(root_index),
            'priority': '1.0',
            'changefreq': 'daily'
        })
        
        # Pages catégories de la racine (sans extension .html)
        root_categories_dir = BASE_DIR / 'page_html' / 'categories'
        if root_categories_dir.exists():
            for html_file in sorted(root_categories_dir.glob('*.html')):
                if html_file.name != 'index.html':
                    # Enlever l'extension .html pour l'URL
                    url_name = html_file.stem
                    root_pages.append({
                        'url': f'{base_domain}/page_html/categories/{url_name}',
                        'lastmod': get_lastmod_date(html_file),
                        'priority': '0.8',
                        'changefreq': 'weekly'
                    })
        
        # Pages produits de la racine (sans extension .html)
        root_products_dir = BASE_DIR / 'page_html' / 'products'
        if root_products_dir.exists():
            for html_file in sorted(root_products_dir.glob('produit-*.html')):
                # Enlever l'extension .html pour l'URL
                url_name = html_file.stem
                root_pages.append({
                    'url': f'{base_domain}/page_html/products/{url_name}',
                    'lastmod': get_lastmod_date(html_file),
                    'priority': '0.7',
                    'changefreq': 'monthly'
                })
        
        # Pages légales de la racine (sans extension .html)
        root_legal_dir = BASE_DIR / 'page_html' / 'legal'
        if root_legal_dir.exists():
            for html_file in sorted(root_legal_dir.glob('*.html')):
                # Enlever l'extension .html pour l'URL
                url_name = html_file.stem
                root_pages.append({
                    'url': f'{base_domain}/page_html/legal/{url_name}',
                    'lastmod': get_lastmod_date(html_file),
                    'priority': '0.5',
                    'changefreq': 'monthly'
                })
        
        if root_pages:
            sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>']
            sitemap_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
            
            for page in root_pages:
                sitemap_content.append('  <url>')
                sitemap_content.append(f'    <loc>{page["url"]}</loc>')
                sitemap_content.append(f'    <lastmod>{page["lastmod"]}</lastmod>')
                sitemap_content.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
                sitemap_content.append(f'    <priority>{page["priority"]}</priority>')
                sitemap_content.append('  </url>')
            
            sitemap_content.append('</urlset>')
            sitemap_en_content = '\n'.join(sitemap_content)
            
            sitemap_file = BASE_DIR / 'sitemap-en.xml'
            sitemap_file.write_text(sitemap_en_content, encoding='utf-8')
            
            # Note: Le sitemap.xml à la racine sera créé plus tard comme sitemap index
            # qui référence tous les sitemaps de langue (c'est mieux pour Google)
            
            page_count = sitemap_en_content.count('<url>')
            print(f"  ✅ {page_count} page(s) ajoutée(s)")
            print(f"  📁 Fichier: {sitemap_file.name} (racine)")
            print(f"  💡 Le sitemap.xml à la racine sera le sitemap index (généré plus tard)")
            generated_sitemaps.append('en')
        else:
            print(f"  ⚠️  Aucune page trouvée pour la racine")
    else:
        print("📝 Génération des sitemaps par langue...")
        print("-" * 70)
    
    # 4. Générer un sitemap pour chaque langue
    for lang_dir in lang_dirs:
        lang_code = lang_dir.name.lower()
        print(f"\n📄 Génération de sitemap-{lang_code}.xml...")
        
        sitemap_content = generate_language_sitemap(lang_dir, lang_code)
        
        if sitemap_content:
            # Sauvegarder le sitemap à la racine (pour Google Search Console)
            sitemap_file = BASE_DIR / f'sitemap-{lang_code}.xml'
            sitemap_file.write_text(sitemap_content, encoding='utf-8')
            
            # Créer aussi un sitemap.xml dans le dossier de langue pour le footer
            lang_sitemap_file = lang_dir / 'sitemap.xml'
            lang_sitemap_file.write_text(sitemap_content, encoding='utf-8')
            
            # Compter les pages
            page_count = sitemap_content.count('<url>')
            print(f"  ✅ {page_count} page(s) ajoutée(s)")
            print(f"  📁 Fichier: {sitemap_file.name} (racine)")
            print(f"  📁 Fichier: {lang_code}/sitemap.xml (pour le footer)")
            generated_sitemaps.append(lang_code)
        else:
            print(f"  ⚠️  Aucune page trouvée, sitemap non généré")
    
    print()
    print("-" * 70)
    
    # 5. Générer le sitemap index à la racine
    print("\n📋 Génération du sitemap index (racine)...")
    sitemap_index_content = generate_sitemap_index(generated_sitemaps)
    
    sitemap_index_file = BASE_DIR / 'sitemap.xml'
    sitemap_index_file.write_text(sitemap_index_content, encoding='utf-8')
    
    print(f"  ✅ Sitemap index généré avec {len(generated_sitemaps)} langue(s)")
    print(f"  📁 Fichier: {sitemap_index_file}")
    print()
    
    # 6. Générer aussi un sitemap combiné (toutes les URLs dans un seul fichier)
    # Utile si Google a des problèmes avec le sitemap index
    print("📋 Génération du sitemap combiné (sitemap-all.xml)...")
    all_pages = []
    
    # Ajouter les pages de la racine (en) si elles existent
    if 'en' in generated_sitemaps:
        root_index = BASE_DIR / 'index.html'
        if root_index.exists():
            all_pages.append({
                'url': f'{base_domain}/',
                'lastmod': get_lastmod_date(root_index),
                'priority': '1.0',
                'changefreq': 'daily'
            })
        
        root_categories_dir = BASE_DIR / 'page_html' / 'categories'
        if root_categories_dir.exists():
            for html_file in sorted(root_categories_dir.glob('*.html')):
                if html_file.name != 'index.html':
                    # Enlever l'extension .html pour l'URL
                    url_name = html_file.stem
                    all_pages.append({
                        'url': f'{base_domain}/page_html/categories/{url_name}',
                        'lastmod': get_lastmod_date(html_file),
                        'priority': '0.8',
                        'changefreq': 'weekly'
                    })
        
        root_products_dir = BASE_DIR / 'page_html' / 'products'
        if root_products_dir.exists():
            for html_file in sorted(root_products_dir.glob('produit-*.html')):
                # Enlever l'extension .html pour l'URL
                url_name = html_file.stem
                all_pages.append({
                    'url': f'{base_domain}/page_html/products/{url_name}',
                    'lastmod': get_lastmod_date(html_file),
                    'priority': '0.7',
                    'changefreq': 'monthly'
                })
    
    # Ajouter les pages de chaque langue
    for lang_dir in lang_dirs:
        lang_code = lang_dir.name.lower()
        lang_pages = find_html_pages(lang_dir, lang_code)
        all_pages.extend(lang_pages)
    
    # Générer le sitemap combiné si on a moins de 50000 URLs (limite Google)
    if len(all_pages) > 0 and len(all_pages) < 50000:
        sitemap_all_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        sitemap_all_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        for page in all_pages:
            sitemap_all_content.append('  <url>')
            sitemap_all_content.append(f'    <loc>{page["url"]}</loc>')
            sitemap_all_content.append(f'    <lastmod>{page["lastmod"]}</lastmod>')
            sitemap_all_content.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
            sitemap_all_content.append(f'    <priority>{page["priority"]}</priority>')
            sitemap_all_content.append('  </url>')
        
        sitemap_all_content.append('</urlset>')
        sitemap_all_file = BASE_DIR / 'sitemap-all.xml'
        sitemap_all_file.write_text('\n'.join(sitemap_all_content), encoding='utf-8')
        
        print(f"  ✅ Sitemap combiné généré avec {len(all_pages)} URL(s)")
        print(f"  📁 Fichier: {sitemap_all_file.name}")
        print()
        print("  💡 Si Google a des problèmes avec sitemap.xml, essayez de soumettre sitemap-all.xml")
    else:
        print(f"  ⚠️  Sitemap combiné non généré ({len(all_pages)} URLs, limite: 50000)")
    print()
    
    # 5. Résumé
    print("=" * 70)
    print("✅ TERMINÉ!")
    print("=" * 70)
    print()
    print("📊 Résumé:")
    print(f"   - Sitemap index: sitemap.xml (racine)")
    for lang_code in generated_sitemaps:
        print(f"   - Sitemap {lang_code}: {lang_code}/sitemap-{lang_code}.xml")
    print()
    print("💡 Pour Google Search Console:")
    print(f"   1. Soumettez uniquement: {base_domain}/sitemap.xml")
    print("   2. Le sitemap index référence automatiquement tous les sitemaps de langue")
    print("   3. Quand vous ajoutez une nouvelle langue, relancez ce script")
    print()
    
    return True

if __name__ == '__main__':
    main()

