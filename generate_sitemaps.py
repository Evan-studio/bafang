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
    
    # Pages catégories
    categories_dir = lang_dir / 'page_html' / 'categories'
    if categories_dir.exists():
        for html_file in sorted(categories_dir.glob('*.html')):
            if html_file.name != 'index.html':  # Exclure les index.html dans les catégories
                pages.append({
                    'url': f'{base_domain}/{lang_code}/page_html/categories/{html_file.name}',
                    'lastmod': get_lastmod_date(html_file),
                    'priority': '0.8',
                    'changefreq': 'weekly'
                })
    
    # Pages produits
    products_dir = lang_dir / 'page_html' / 'products'
    if products_dir.exists():
        for html_file in sorted(products_dir.glob('produit-*.html')):
            pages.append({
                'url': f'{base_domain}/{lang_code}/page_html/products/{html_file.name}',
                'lastmod': get_lastmod_date(html_file),
                'priority': '0.7',
                'changefreq': 'monthly'
            })
    
    # Pages légales
    legal_dir = lang_dir / 'page_html' / 'legal'
    if legal_dir.exists():
        for html_file in sorted(legal_dir.glob('*.html')):
            pages.append({
                'url': f'{base_domain}/{lang_code}/page_html/legal/{html_file.name}',
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

def generate_sitemap_index(lang_dirs):
    """Génère le sitemap index qui référence tous les sitemaps de langue."""
    base_domain = get_base_domain()
    today = datetime.now().strftime('%Y-%m-%d')
    
    sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_content.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for lang_dir in lang_dirs:
        lang_code = lang_dir.name.lower()
        sitemap_url = f'{base_domain}/sitemap-{lang_code}.xml'
        sitemap_content.append('  <sitemap>')
        sitemap_content.append(f'    <loc>{sitemap_url}</loc>')
        sitemap_content.append(f'    <lastmod>{today}</lastmod>')
        sitemap_content.append('  </sitemap>')
    
    sitemap_content.append('</sitemapindex>')
    
    return '\n'.join(sitemap_content)

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🗺️  GÉNÉRATION DES SITEMAPS MULTILINGUES")
    print("=" * 70)
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
    
    # 3. Générer un sitemap pour chaque langue
    print("📝 Génération des sitemaps par langue...")
    print("-" * 70)
    
    generated_sitemaps = []
    
    for lang_dir in lang_dirs:
        lang_code = lang_dir.name.lower()
        print(f"\n📄 Génération de sitemap-{lang_code}.xml...")
        
        sitemap_content = generate_language_sitemap(lang_dir, lang_code)
        
        if sitemap_content:
            # Sauvegarder le sitemap à la racine (pour Google Search Console)
            sitemap_file = BASE_DIR / f'sitemap-{lang_code}.xml'
            sitemap_file.write_text(sitemap_content, encoding='utf-8')
            
            # Compter les pages
            page_count = sitemap_content.count('<url>')
            print(f"  ✅ {page_count} page(s) ajoutée(s)")
            print(f"  📁 Fichier: {sitemap_file.name} (racine)")
            generated_sitemaps.append(lang_code)
        else:
            print(f"  ⚠️  Aucune page trouvée, sitemap non généré")
    
    print()
    print("-" * 70)
    
    # 4. Générer le sitemap index à la racine
    print("\n📋 Génération du sitemap index (racine)...")
    sitemap_index_content = generate_sitemap_index(lang_dirs)
    
    sitemap_index_file = BASE_DIR / 'sitemap.xml'
    sitemap_index_file.write_text(sitemap_index_content, encoding='utf-8')
    
    print(f"  ✅ Sitemap index généré avec {len(generated_sitemaps)} langue(s)")
    print(f"  📁 Fichier: {sitemap_index_file}")
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

