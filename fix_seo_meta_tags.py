#!/usr/bin/env python3
"""
Script pour corriger les balises SEO (Open Graph, Twitter Card, Canonical, Schema.org)
qui pointent vers l'ancien domaine uni-ion.com au lieu de bafang-shop.com

Ce script :
1. Détecte automatiquement toutes les langues
2. Corrige les balises dans index.html de chaque langue
3. Corrige les balises dans toutes les pages produits et catégories
4. Met à jour les URLs avec le bon domaine depuis translations.csv
"""

import re
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
EXCLUDED_DIRS = {
    'APPLI:SCRIPT aliexpress', 'scripts', 'config', 'images', 'page_html', 
    'upload_cloudflare', 'sauv', 'CSV', '__pycache__', '.git', 'node_modules',
    'upload youtube'
}

def get_domain_from_csv(lang_dir):
    """Récupère le domaine depuis translations.csv."""
    translations_csv = lang_dir / 'translations.csv'
    if not translations_csv.exists():
        return None
    
    try:
        with open(translations_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('key', '').strip() == 'site.domain':
                    # Chercher dans toutes les colonnes
                    for col in reader.fieldnames:
                        url = row.get(col, '').strip()
                        if url and url.startswith('http'):
                            return url.rstrip('/')
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la lecture de translations.csv: {e}")
    
    return None

def detect_languages():
    """Détecte automatiquement toutes les langues."""
    languages = []
    
    # Ajouter le dossier principal (en)
    root_index = BASE_DIR / 'index.html'
    root_translations = BASE_DIR / 'translations.csv'
    if root_index.exists() and root_translations.exists():
        languages.append({
            'code': 'en',
            'dir': BASE_DIR,
            'domain': get_domain_from_csv(BASE_DIR) or 'https://bafang-shop.com'
        })
    
    # Détecter les dossiers de langue
    for item in BASE_DIR.iterdir():
        if (item.is_dir() and 
            not item.name.startswith('.') and 
            item.name not in EXCLUDED_DIRS and
            (item / 'index.html').exists() and 
            (item / 'translations.csv').exists()):
            
            lang_code = item.name.lower()
            domain = get_domain_from_csv(item) or f'https://bafang-shop.com/{lang_code}'
            languages.append({
                'code': lang_code,
                'dir': item,
                'domain': domain
            })
    
    return languages

def fix_meta_tags_in_html(html_content, lang_code, domain, is_index=False):
    """Corrige les balises meta dans le contenu HTML."""
    fixed = False
    
    # Construire l'URL de base
    if lang_code == 'en':
        base_url = domain
    else:
        base_url = f"{domain}/{lang_code}"
    
    # 1. Supprimer les balises Open Graph et Twitter Card incorrectes (uni-ion.com)
    old_og_pattern = r'<meta property="og:title"[^>]*>.*?<link rel="canonical" href="https://uni-ion\.com[^"]*">'
    if re.search(old_og_pattern, html_content, re.DOTALL):
        html_content = re.sub(old_og_pattern, '', html_content, flags=re.DOTALL)
        fixed = True
    
    # 2. Supprimer les balises OG/Twitter individuelles qui pointent vers uni-ion.com
    html_content = re.sub(
        r'<meta property="og:[^"]*" content="https://uni-ion\.com[^"]*">',
        '',
        html_content
    )
    html_content = re.sub(
        r'<meta name="twitter:[^"]*" content="https://uni-ion\.com[^"]*">',
        '',
        html_content
    )
    
    # 3. Supprimer les canonical en double qui pointent vers uni-ion.com
    html_content = re.sub(
        r'<link rel="canonical" href="https://uni-ion\.com[^"]*">',
        '',
        html_content
    )
    
    # 4. Corriger le Schema.org JSON-LD
    schema_pattern = r'<script type="application/ld\+json">\s*({[^}]*"url"\s*:\s*"https://uni-ion\.com[^}]*})'
    def replace_schema(match):
        schema_json = match.group(1)
        # Remplacer uni-ion.com par le bon domaine
        new_schema = schema_json.replace('https://uni-ion.com', base_url)
        return f'<script type="application/ld+json">\n{new_schema}'
    
    if re.search(schema_pattern, html_content, re.DOTALL):
        html_content = re.sub(schema_pattern, replace_schema, html_content, flags=re.DOTALL)
        fixed = True
    
    return html_content, fixed

def fix_html_file(file_path, lang_code, domain, file_type='index'):
    """Corrige un fichier HTML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content, fixed = fix_meta_tags_in_html(content, lang_code, domain, file_type == 'index')
        
        if fixed and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la correction de {file_path}: {e}")
        return False

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🔧 CORRECTION DES BALISES SEO")
    print("=" * 70)
    print()
    
    languages = detect_languages()
    
    if not languages:
        print("❌ Aucune langue détectée")
        return
    
    print(f"✅ {len(languages)} langue(s) détectée(s)")
    print()
    
    total_fixed = 0
    
    for lang in languages:
        lang_code = lang['code']
        lang_dir = lang['dir']
        domain = lang['domain']
        
        print(f"🌍 Langue: {lang_code.upper()}")
        print(f"   Domaine: {domain}")
        
        fixed_count = 0
        
        # Corriger index.html
        index_file = lang_dir / 'index.html'
        if index_file.exists():
            if fix_html_file(index_file, lang_code, domain, 'index'):
                fixed_count += 1
                print(f"  ✅ index.html corrigé")
        
        # Corriger les pages produits
        products_dir = lang_dir / 'page_html' / 'products'
        if products_dir.exists():
            product_files = list(products_dir.glob('*.html'))
            for product_file in product_files:
                if fix_html_file(product_file, lang_code, domain, 'product'):
                    fixed_count += 1
            if product_files:
                print(f"  ✅ {len(product_files)} page(s) produit(s) vérifiée(s)")
        
        # Corriger les pages catégories
        categories_dir = lang_dir / 'page_html' / 'categories'
        if categories_dir.exists():
            category_files = list(categories_dir.glob('*.html'))
            for category_file in category_files:
                if fix_html_file(category_file, lang_code, domain, 'category'):
                    fixed_count += 1
            if category_files:
                print(f"  ✅ {len(category_files)} page(s) catégorie(s) vérifiée(s)")
        
        # Corriger les pages légales
        legal_dir = lang_dir / 'page_html' / 'legal'
        if legal_dir.exists():
            legal_files = list(legal_dir.glob('*.html'))
            for legal_file in legal_files:
                if fix_html_file(legal_file, lang_code, domain, 'legal'):
                    fixed_count += 1
            if legal_files:
                print(f"  ✅ {len(legal_files)} page(s) légale(s) vérifiée(s)")
        
        total_fixed += fixed_count
        print()
    
    print("=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print(f"✅ {total_fixed} fichier(s) corrigé(s)")
    print()
    print("💡 Les balises Open Graph, Twitter Card et Schema.org")
    print("   qui pointaient vers uni-ion.com ont été supprimées.")
    print("   Les balises canonical correctes sont conservées.")
    print("=" * 70)

if __name__ == '__main__':
    main()





