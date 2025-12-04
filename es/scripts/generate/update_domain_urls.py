#!/usr/bin/env python3
"""
Script pour mettre à jour toutes les URLs du site avec le domaine défini dans translations.csv.

Ce script :
1. Lit le domaine depuis translations.csv (clé: site.domain)
2. Remplace toutes les URLs dans index.html et toutes les pages générées
3. Met à jour les meta tags (Open Graph, Twitter, canonical, hreflang, schema.org)

Usage:
    python3 scripts/generate/update_domain_urls.py
"""

import csv
import re
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent.parent.parent
TRANSLATIONS_CSV = BASE_DIR / 'translations.csv'
INDEX_HTML = BASE_DIR / 'index.html'

def load_domain_from_csv():
    """Charge le domaine depuis translations.csv (colonne 'en')."""
    if not TRANSLATIONS_CSV.exists():
        print(f"❌ Fichier non trouvé: {TRANSLATIONS_CSV}")
        return None
    
    try:
        with open(TRANSLATIONS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get('key', '').strip()
                if key == 'site.domain':
                    domain = row.get('en', '').strip()
                    if domain and not domain.startswith('='):
                        # S'assurer que le domaine se termine par / pour la racine
                        if not domain.endswith('/'):
                            domain = domain.rstrip('/')
                        return domain
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return None
    
    print("⚠️  Clé 'site.domain' non trouvée dans translations.csv")
    return None

def extract_base_domain(url):
    """Extrait le domaine de base d'une URL."""
    if not url or not url.startswith('http'):
        return None
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def update_urls_in_content(content, old_domain, new_domain):
    """Remplace toutes les URLs dans le contenu HTML."""
    if not old_domain or not new_domain:
        return content
    
    # Normaliser les domaines (sans / à la fin pour la base)
    old_base = old_domain.rstrip('/')
    new_base = new_domain.rstrip('/')
    
    # Extraire le nom de domaine (sans protocole) pour les remplacements
    old_domain_name = old_base.replace('http://', '').replace('https://', '')
    new_domain_name = new_base.replace('http://', '').replace('https://', '')
    
    # Remplacer seulement les URLs complètes (pas les attributs xmlns, etc.)
    # Pattern 1: URLs complètes dans les attributs href="..." et content="..."
    content = re.sub(
        rf'(href|content)="https?://{re.escape(old_domain_name)}([^"]*)"',
        rf'\1="{new_base}\2"',
        content
    )
    
    # Pattern 2: URLs dans les balises <link> et <meta>
    content = re.sub(
        rf'(<link[^>]+(?:href|rel)=")https?://{re.escape(old_domain_name)}([^"]*)"',
        rf'\1{new_base}\2"',
        content
    )
    
    # Pattern 3: URLs dans JSON-LD schema.org
    content = re.sub(
        rf'"url":\s*"https?://{re.escape(old_domain_name)}([^"]*)"',
        f'"url": "{new_base}\\1"',
        content
    )
    
    # Pattern 4: URLs dans les balises hreflang
    content = re.sub(
        rf'(<link[^>]+hreflang="[^"]+"[^>]+href=")https?://{re.escape(old_domain_name)}([^"]*)"',
        rf'\1{new_base}\2"',
        content
    )
    
    # Pattern 5: URLs complètes standalone (pas dans les attributs)
    # Seulement si c'est une URL complète avec chemin
    content = re.sub(
        rf'https?://{re.escape(old_domain_name)}(/[^\s"\'<>]*)',
        rf'{new_base}\1',
        content
    )
    
    return content

def find_old_domain_in_content(content):
    """Trouve l'ancien domaine dans le contenu."""
    # Chercher les patterns connus
    known_patterns = [
        r'https?://votresite\.com',
        r'https?://localhost:\d+',
        r'https?://makita-shop\.pages\.dev',
    ]
    
    for pattern in known_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(0)
    
    # Chercher n'importe quelle URL
    url_match = re.search(r'https?://[^\s"\'<>/]+', content)
    if url_match:
        url = url_match.group(0)
        # Vérifier que ce n'est pas un lien externe (aliexpress, google, etc.)
        if 'aliexpress.com' not in url and 'google.com' not in url and 'policies.google.com' not in url:
            return extract_base_domain(url)
    
    return None

def update_index_html(new_domain):
    """Met à jour toutes les URLs dans index.html."""
    if not INDEX_HTML.exists():
        print(f"❌ Fichier non trouvé: {INDEX_HTML}")
        return False
    
    try:
        content = INDEX_HTML.read_text(encoding='utf-8')
        original_content = content
        
        # Trouver l'ancien domaine
        old_domain = find_old_domain_in_content(content)
        
        if old_domain:
            print(f"  🔄 Remplacement: {old_domain} → {new_domain}")
            content = update_urls_in_content(content, old_domain, new_domain)
        else:
            print(f"  ⚠️  Aucun ancien domaine détecté, vérification manuelle recommandée")
        
        # Sauvegarder seulement si changé
        if content != original_content:
            INDEX_HTML.write_text(content, encoding='utf-8')
            print(f"  ✅ index.html mis à jour")
        else:
            print(f"  ℹ️  index.html déjà à jour")
        return True
    except Exception as e:
        print(f"  ❌ Erreur lors de la mise à jour de index.html: {e}")
        return False

def update_generated_pages(new_domain):
    """Met à jour toutes les URLs dans les pages générées."""
    pages_dirs = [
        BASE_DIR / 'page_html' / 'categories',
        BASE_DIR / 'page_html' / 'products',
        BASE_DIR / 'page_html' / 'legal',
    ]
    
    updated_count = 0
    
    for pages_dir in pages_dirs:
        if not pages_dir.exists():
            continue
        
        html_files = list(pages_dir.rglob('*.html'))
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                original_content = content
                
                # Trouver l'ancien domaine
                old_domain = find_old_domain_in_content(content)
                
                if old_domain and old_domain != new_domain:
                    content = update_urls_in_content(content, old_domain, new_domain)
                
                if content != original_content:
                    html_file.write_text(content, encoding='utf-8')
                    updated_count += 1
            except Exception as e:
                print(f"  ⚠️  Erreur avec {html_file.name}: {e}")
    
    if updated_count > 0:
        print(f"  ✅ {updated_count} page(s) générée(s) mise(s) à jour")
    else:
        print(f"  ℹ️  Aucune page générée à mettre à jour")
    
    return updated_count

def update_sitemap(new_domain):
    """Met à jour les URLs dans le sitemap.xml et sitemap.html."""
    sitemap_xml = BASE_DIR / 'sitemap.xml'
    sitemap_html = BASE_DIR / 'sitemap.html'
    
    updated = False
    
    # Mettre à jour sitemap.xml
    if sitemap_xml.exists():
        try:
            content = sitemap_xml.read_text(encoding='utf-8')
            original_content = content
            
            old_domain = find_old_domain_in_content(content)
            if old_domain and old_domain != new_domain:
                content = update_urls_in_content(content, old_domain, new_domain)
            
            if content != original_content:
                sitemap_xml.write_text(content, encoding='utf-8')
                print(f"  ✅ sitemap.xml mis à jour")
                updated = True
            else:
                print(f"  ℹ️  sitemap.xml déjà à jour")
        except Exception as e:
            print(f"  ⚠️  Erreur avec sitemap.xml: {e}")
    else:
        print(f"  ℹ️  sitemap.xml non trouvé (optionnel)")
    
    # Mettre à jour sitemap.html
    if sitemap_html.exists():
        try:
            content = sitemap_html.read_text(encoding='utf-8')
            original_content = content
            
            old_domain = find_old_domain_in_content(content)
            if old_domain and old_domain != new_domain:
                content = update_urls_in_content(content, old_domain, new_domain)
            
            if content != original_content:
                sitemap_html.write_text(content, encoding='utf-8')
                print(f"  ✅ sitemap.html mis à jour")
                updated = True
            else:
                print(f"  ℹ️  sitemap.html déjà à jour")
        except Exception as e:
            print(f"  ⚠️  Erreur avec sitemap.html: {e}")
    else:
        print(f"  ℹ️  sitemap.html non trouvé (optionnel)")
    
    return updated

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🌐 MISE À JOUR DES URLs AVEC LE DOMAINE DU CSV")
    print("=" * 70)
    print()
    
    # 1. Charger le domaine depuis le CSV
    print("📖 Chargement du domaine depuis translations.csv...")
    new_domain = load_domain_from_csv()
    
    if not new_domain:
        print("❌ Impossible de charger le domaine. Vérifiez que 'site.domain' existe dans translations.csv")
        return False
    
    print(f"✅ Domaine trouvé: {new_domain}")
    print()
    
    # 2. Mettre à jour index.html
    print("📄 Mise à jour de index.html...")
    update_index_html(new_domain)
    print()
    
    # 3. Mettre à jour les pages générées
    print("📄 Mise à jour des pages générées...")
    update_generated_pages(new_domain)
    print()
    
    # 4. Mettre à jour le sitemap
    print("🗺️  Mise à jour du sitemap...")
    update_sitemap(new_domain)
    print()
    
    print("=" * 70)
    print("✅ TERMINÉ!")
    print("=" * 70)
    print()
    print(f"💡 Toutes les URLs ont été mises à jour avec: {new_domain}")
    print("💡 Pour changer le domaine, modifiez 'site.domain' dans translations.csv et relancez ce script.")
    print()
    
    return True

if __name__ == "__main__":
    main()

