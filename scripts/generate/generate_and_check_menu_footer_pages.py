#!/usr/bin/env python3
"""
Script pour générer et vérifier les pages HTML du menu (catégories) et du footer (pages légales).

Le script lit DIRECTEMENT le CSV pour savoir :
- Quels éléments mettre dans le menu (menu.*)
- Quels éléments mettre dans le footer (footer.link.*)
- Génère chaque page avec le bon menu et le bon footer depuis le CSV

Usage:
    python3 scripts/generate/generate_and_check_menu_footer_pages.py
"""

import csv
import re
import unicodedata
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).parent.parent.parent
TRANSLATIONS_CSV = BASE_DIR / 'translations.csv'
PRODUCTS_CSV = BASE_DIR / 'CSV' / 'all_products.csv'
TEMPLATE_CATEGORY = BASE_DIR / 'page_html' / 'templates' / 'category.html'
CATEGORIES_DIR = BASE_DIR / 'page_html' / 'categories'
LEGAL_DIR = BASE_DIR / 'page_html' / 'legal'

def slugify(text):
    """Convertit un texte en slug (minuscules, tirets, sans accents)."""
    if not text:
        return ''
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = unicodedata.normalize('NFD', slug)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    slug = slug.strip('-')
    return slug

def detect_language_code():
    """Détecte le code de langue depuis le nom du dossier (fr, de, es, etc.)."""
    base_name = BASE_DIR.name.lower()
    # Si le nom du dossier est une langue (2 lettres), c'est la langue cible
    if len(base_name) == 2 and base_name.isalpha():
        return base_name
    # Sinon, par défaut anglais
    return 'en'

def load_translations_from_csv():
    """Charge toutes les traductions depuis translations.csv (colonne détectée automatiquement)."""
    translations = {}
    
    if not TRANSLATIONS_CSV.exists():
        print(f"❌ Fichier non trouvé: {TRANSLATIONS_CSV}")
        return translations
    
    # Détecter la langue du dossier
    lang_code = detect_language_code()
    
    try:
        with open(TRANSLATIONS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Chercher la colonne de langue : {lang_code}_auto en priorité, puis {lang_code}, puis 'en'
            lang_col = None
            if f'{lang_code}_auto' in fieldnames:
                lang_col = f'{lang_code}_auto'
            elif lang_code in fieldnames:
                lang_col = lang_code
            else:
                lang_col = 'en'  # Fallback sur anglais
            
            for row in reader:
                key = row.get('key', '').strip()
                if key:
                    # Utiliser la colonne détectée
                    value = row.get(lang_col, '').strip()
                    # Ignorer les formules (commencent par =) et les cellules vides
                    if value and not value.startswith('='):
                        translations[key] = value
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return translations
    
    return translations

def get_translation(key, translations, default=''):
    """Récupère une traduction depuis le dictionnaire."""
    return translations.get(key, default)

def escape_html_attr(text):
    """Échappe les caractères spéciaux pour les attributs HTML."""
    if not text:
        return ""
    return escape(text).replace('"', '&quot;')

def load_products_from_csv():
    """Charge tous les produits depuis all_products.csv (avec colonnes traduites si disponibles)."""
    products = []
    
    if not PRODUCTS_CSV.exists():
        print(f"⚠️  Fichier produits non trouvé: {PRODUCTS_CSV}")
        return products
    
    # Détecter la langue du dossier
    lang_code = detect_language_code()
    
    try:
        with open(PRODUCTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Chercher les colonnes traduites : {col}_{lang_code}_auto en priorité, puis {col}
            def get_translated_col(base_col):
                """Retourne la colonne traduite si disponible."""
                auto_col = f'{base_col}_{lang_code}_auto'
                if auto_col in fieldnames:
                    return auto_col
                elif base_col in fieldnames:
                    return base_col
                return None
            
            name_col = get_translated_col('name') or get_translated_col('titre')
            
            for row in reader:
                product_id = row.get('product_id', '').strip()
                if not product_id:
                    continue
                
                category_id = row.get('category_id', '').strip()
                titre = row.get('titre', '').strip() if 'titre' in fieldnames else ''
                name = row.get(name_col, '').strip() if name_col else ''
                title = name or titre or row.get('name', '').strip() or row.get('titre', '').strip()
                
                affiliate_link = row.get('affiliate_links', '').strip()
                image_paths = row.get('image_paths', '').strip()
                
                products.append({
                    'id': product_id,
                    'category_id': category_id,
                    'title': title,
                    'name': name or titre,
                    'affiliate_link': affiliate_link,
                    'image_paths': image_paths
                })
    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture des produits: {e}")
        return products
    
    return products

def extract_first_image(image_paths_str, product_id):
    """Extrait le premier chemin d'image et le convertit en chemin relatif."""
    # Nettoyer le product_id (enlever l'apostrophe si présente)
    clean_product_id = str(product_id).strip().lstrip("'")
    
    # Pour une page catégorie, le chemin est toujours: ../../../images/products/{product_id}/image_1.jpg
    # Les images sont dans le dossier parent, donc ../../../images/
    # Le CSV peut contenir des chemins absolus, mais on utilise toujours le format standard
    if not image_paths_str or not product_id:
        return f"../../../images/products/{clean_product_id}/image_1.jpg"
    
    # Les images sont séparées par |
    images = image_paths_str.split('|')
    if not images:
        return f"../../../images/products/{clean_product_id}/image_1.jpg"
    
    first_image = images[0].strip()
    
    # Extraire le nom du fichier (image_1.jpg, image_2.jpg, etc.)
    filename = Path(first_image).name
    
    # Utiliser toujours le format standard: ../../../images/products/{product_id}/{filename}
    return f"../../../images/products/{clean_product_id}/{filename}"

def generate_product_html(product, translations):
    """Génère le HTML pour une carte produit."""
    product_id = product['id']
    # Utiliser 'name' en priorité, puis 'title' comme fallback
    title = product.get('name', '') or product.get('title', '') or 'Product'
    affiliate_link = product['affiliate_link'] or '#'
    image_path = extract_first_image(product.get('image_paths', ''), product_id)
    
    # Générer un nombre de reviews aléatoire mais cohérent (basé sur product_id)
    import random
    try:
        # Nettoyer le product_id et extraire les 6 derniers chiffres
        clean_id = str(product_id).strip().lstrip("'").replace('.', '').replace('E+', '').replace('e+', '')
        if clean_id and len(clean_id) >= 6:
            seed_value = int(clean_id[-6:])
        else:
            seed_value = None
    except (ValueError, AttributeError):
        seed_value = None
    random.seed(seed_value)
    reviews_count = random.randint(15, 150)
    random.seed()  # Réinitialiser le seed
    
    title_escaped = escape_html_attr(title)
    button_text = get_translation('button.view_on_aliexpress', translations, 'View on AliExpress')
    
    # Image avec fallback
    img_tag = f'<img src="{image_path}" alt="{title_escaped}" class="product-image" loading="lazy" onerror="this.onerror=null;this.src=\'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'300\' height=\'300\'%3E%3Crect fill=\'%23f5f5f5\' width=\'300\' height=\'300\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' fill=\'%23999\' font-family=\'Arial\' font-size=\'14\'%3EImage%3C/text%3E%3C/svg%3E\'">'
    
    html = f'''<article class="product-card">
<a href="../products/produit-{product_id}.html" style="text-decoration:none;color:inherit">
{img_tag}
<div class="product-info">
<h2 class="product-title">{title_escaped}</h2>
<div class="product-rating">
<span class="product-stars">★★★★★</span>
<span class="product-reviews">({reviews_count})</span>
</div>
<a href="{affiliate_link}" class="cta-button" target="_blank" rel="noopener noreferrer">{escape_html_attr(button_text)}</a>
</div>
</a>
</article>'''
    
    return html

def generate_products_html_for_category(category_id, all_products, translations):
    """Génère le HTML des produits pour une catégorie donnée."""
    # Filtrer les produits par category_id
    category_products = [p for p in all_products if p.get('category_id', '') == category_id]
    
    if not category_products:
        return '<div class="loading">No products available for this category.</div>'
    
    # Afficher tous les produits (pas de limite)
    products_html = []
    for product in category_products:
        products_html.append(generate_product_html(product, translations))
    
    return '\n'.join(products_html)

def get_menu_items_from_csv(translations, page_type='category'):
    """
    Lit le CSV et retourne la liste des éléments du menu.
    page_type: 'category' ou 'legal'
    """
    menu_items = []
    
    # Home (depuis footer.link.home)
    home_text = get_translation('footer.link.home', translations, 'Home')
    if page_type == 'category':
        menu_items.append({'text': home_text, 'url': '../../'})
    else:  # legal
        menu_items.append({'text': home_text, 'url': '../../'})
    
    # Toutes les catégories (menu.*) - utiliser des numéros (1, 2, 3...)
    menu_keys = [k for k in translations.keys() if k.startswith('menu.') and k != 'home.en']
    menu_keys_sorted = sorted(menu_keys)
    
    for index, menu_key in enumerate(menu_keys_sorted, start=1):
        menu_name = translations.get(menu_key, '')
        if not menu_name:
            continue
        
        # Utiliser le numéro comme slug (1, 2, 3, etc.)
        category_number = str(index)
        
        if page_type == 'category':
            menu_items.append({'text': menu_name, 'url': f"{category_number}.html"})  # Même dossier
        else:  # legal
            menu_items.append({'text': menu_name, 'url': f"../categories/{category_number}.html"})  # Vers categories/
    
    return menu_items

def get_footer_items_from_csv(translations, page_type='category'):
    """
    Lit le CSV et retourne la liste des éléments du footer.
    Home est TOUJOURS en premier.
    page_type: 'category' ou 'legal'
    """
    footer_items = []
    
    # 1. Home EN PREMIER
    home_key = None
    sitemap_key = None
    legal_keys = []
    
    footer_keys = [k for k in translations.keys() if k.startswith('footer.link.')]
    for footer_key in footer_keys:
        if 'home' in footer_key:
            home_key = footer_key
        elif 'sitemap' in footer_key:
            sitemap_key = footer_key
        else:
            legal_keys.append(footer_key)
    
    # Ajouter Home en premier
    if home_key:
        home_text = translations.get(home_key, '')
        if home_text:
            if page_type == 'category':
                footer_items.append({'text': home_text, 'url': '../../'})
            else:  # legal
                footer_items.append({'text': home_text, 'url': '../../'})
    
    # 2. Sitemap en deuxième
    if sitemap_key:
        sitemap_text = translations.get(sitemap_key, '')
        if sitemap_text:
            if page_type == 'category':
                footer_items.append({'text': sitemap_text, 'url': '../../sitemap.xml'})
            else:  # legal
                footer_items.append({'text': sitemap_text, 'url': '../../sitemap.xml'})
    
    # 3. Pages légales ensuite (triées)
    for footer_key in sorted(legal_keys):
        text = translations.get(footer_key, '')
        if not text:
            continue
        
        slug = slugify(text)
        if page_type == 'category':
            footer_items.append({'text': text, 'url': f"../legal/{slug}.html"})
        else:  # legal
            footer_items.append({'text': text, 'url': f"{slug}.html"})  # Même dossier
    
    return footer_items

def generate_menu_html(menu_items):
    """Génère le HTML du menu depuis la liste des items."""
    menu_html = []
    for item in menu_items:
        menu_text = item["text"].upper()  # Menu en majuscule
        menu_html.append(f'<li><a href="{item["url"]}">{escape_html_attr(menu_text)}</a></li>')
    return '\n'.join(menu_html)

def generate_footer_html(footer_items, translations):
    """Génère le HTML du footer depuis la liste des items."""
    footer_html = '<div class="footer-links">\n'
    for item in footer_items:
        footer_html += f'<a href="{item["url"]}">{escape_html_attr(item["text"])}</a>\n'
    footer_html += '</div>\n'
    
    # Contact et copyright
    footer_contact = get_translation('footer.contact', translations, 'Contact us:')
    footer_copyright = get_translation('footer.copyright', translations, '© 2024 AliExpress Affiliate. All rights reserved.')
    contact_email = get_translation('site.contact.email', translations, 'contact@naturehike-shop.com')
    
    footer_html += f'<p>{escape_html_attr(footer_contact)} <a href="mailto:{escape_html_attr(contact_email)}">{escape_html_attr(contact_email)}</a></p>\n'
    footer_html += f'<p>{escape_html_attr(footer_copyright)}</p>'
    
    return footer_html

def update_menu_and_footer_in_page(html_content, menu_items, footer_items, translations):
    """Remplace le menu et le footer dans une page HTML."""
    # Générer le menu HTML
    menu_html = generate_menu_html(menu_items)
    
    # Remplacer le menu
    html_content = re.sub(
        r'<ul[^>]*class="menu"[^>]*>.*?</ul>',
        f'<ul class="menu" id="menu">\n{menu_html}\n</ul>',
        html_content,
        flags=re.DOTALL
    )
    
    # Générer le footer HTML
    footer_html = generate_footer_html(footer_items, translations)
    
    # Remplacer le footer
    html_content = re.sub(
        r'<footer>.*?</footer>',
        f'<footer>\n{footer_html}\n</footer>',
        html_content,
        flags=re.DOTALL
    )
    
    # Corriger le chemin de la favicon si nécessaire (pour les pages catégories)
    # Les pages catégories sont dans page_html/categories/, donc elles doivent remonter de 3 niveaux
    html_content = re.sub(
        r'href="\.\./\.\./images/favicon/favicon\.ico"',
        r'href="../../../images/favicon/favicon.ico"',
        html_content
    )
    
    # Corriger le chemin du logo si nécessaire (../../images/logo -> ../../../images/logo pour les pages catégories)
    html_content = re.sub(
        r'src="\.\./\.\./images/logo/logo\.webp"',
        r'src="../../../images/logo/logo.webp"',
        html_content
    )
    
    return html_content

def generate_category_page(category_slug, category_name, translations, all_products=None):
    """Génère une page catégorie depuis le template."""
    if not TEMPLATE_CATEGORY.exists():
        print(f"❌ Template non trouvé: {TEMPLATE_CATEGORY}")
        return None
    
    with open(TEMPLATE_CATEGORY, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Récupérer menu et footer depuis CSV
    menu_items = get_menu_items_from_csv(translations, page_type='category')
    footer_items = get_footer_items_from_csv(translations, page_type='category')
    
    # Mettre à jour menu et footer
    html = update_menu_and_footer_in_page(html, menu_items, footer_items, translations)
    
    # Corriger la langue dans le tag html
    lang_code = detect_language_code()
    html = re.sub(r'<html lang="[^"]*"', f'<html lang="{lang_code}"', html)
    html = re.sub(r"<html lang='[^']*'", f'<html lang="{lang_code}"', html)
    
    # Mettre à jour les infos de la catégorie
    # Utiliser le numéro (category_slug est maintenant un numéro)
    category_title = get_translation(f'meta.title.menu.{category_slug}', translations, f'{category_name} - AliExpress Affiliate')
    category_description = get_translation(f'meta.des.menu.{category_slug}', translations, f'Discover our selection of {category_name}')
    category_content = get_translation(f'descripton.{category_slug}', translations, '')
    
    html = re.sub(r'<title>.*?</title>', f'<title>{escape_html_attr(category_title)}</title>', html)
    html = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{escape_html_attr(category_description)}">', html)
    
    # Mettre à jour le h1 et ajouter la description en une seule opération
    h1_html = f'<h1 class="section-title">{escape_html_attr(category_name)}</h1>'
    if category_content:
        description_html = f'<div class="category-description">\n<p>{escape_html_attr(category_content)}</p>\n</div>'
        h1_html += f'\n{description_html}'
        print(f"  ✅ Description ajoutée pour {category_name} ({len(category_content)} caractères)")
    else:
        print(f"  ⚠️  Pas de description pour {category_name} (clé: descripton.{category_slug})")
    
    # Utiliser une regex plus flexible pour trouver le h1
    html = re.sub(
        r'<h1[^>]*class="section-title"[^>]*>.*?</h1>',
        h1_html,
        html
    )
    
    # Générer les produits pour cette catégorie
    if all_products:
        products_html = generate_products_html_for_category(category_slug, all_products, translations)
        # Remplacer tout le contenu entre products-container et </main>
        html = re.sub(
            r'(<div id="products-container" class="products-grid">).*?(</main>)',
            rf'\1\n{products_html}\n</div>\2',
            html,
            flags=re.DOTALL
        )
    
    return html

def generate_legal_page(legal_key, legal_text, translations):
    """Génère une page légale depuis le template."""
    if not TEMPLATE_CATEGORY.exists():
        print(f"❌ Template non trouvé: {TEMPLATE_CATEGORY}")
        return None
    
    with open(TEMPLATE_CATEGORY, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Récupérer menu et footer depuis CSV
    menu_items = get_menu_items_from_csv(translations, page_type='legal')
    footer_items = get_footer_items_from_csv(translations, page_type='legal')
    
    # Mettre à jour menu et footer
    html = update_menu_and_footer_in_page(html, menu_items, footer_items, translations)
    
    # Mettre à jour les infos de la page légale
    legal_slug = legal_key.replace('footer.link.', '')
    legal_title = get_translation(f'legal.{legal_slug}.title', translations, f'{legal_text} - AliExpress Affiliate')
    legal_description = get_translation(f'legal.{legal_slug}.meta.description', translations, f'{legal_text}')
    legal_content = get_translation(f'legal.{legal_slug}.content', translations, '')
    
    html = re.sub(r'<title>.*?</title>', f'<title>{escape_html_attr(legal_title)}</title>', html)
    html = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{escape_html_attr(legal_description)}">', html)
    
    # Remplacer la section main avec mise en forme HTML
    content_html = f'<section>\n<h1>{escape_html_attr(legal_title)}</h1>\n'
    if legal_content:
        # Si le contenu contient déjà du HTML (comme about-us), l'utiliser tel quel
        if legal_content.strip().startswith('<'):
            # Contenu déjà en HTML
            content_html += legal_content + '\n'
        else:
            # Formater le contenu : détecter les sections numérotées
            # Le contenu peut être sur une seule ligne ou plusieurs lignes
            # D'abord, essayer de diviser par les numéros de section (1., 2., 3., etc.)
            # Pattern pour détecter le début d'une section: chiffre suivi d'un point et d'un espace
            sections = re.split(r'(\d+\.\s+)', legal_content)
            
            # Si on a trouvé des sections, les traiter
            if len(sections) > 1:
                i = 0
                # Traiter le texte avant la première section (s'il existe)
                if sections[0].strip() and not re.match(r'^\d+\.\s+$', sections[0]):
                    text = sections[0].strip()
                    if text:
                        content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(text)}</p>\n'
                    i = 1
                
                while i < len(sections):
                    if re.match(r'^\d+\.\s+$', sections[i]):
                        # C'est un numéro de section
                        section_num = sections[i].strip()
                        section_text = sections[i+1] if i+1 < len(sections) else ''
                        section_text = section_text.strip()
                        
                        if section_text:
                            # Chercher le premier ":" pour séparer titre et contenu
                            if ':' in section_text:
                                parts = section_text.split(':', 1)
                                title_part = parts[0].strip()
                                content_part = parts[1].strip() if len(parts) > 1 else ''
                                
                                # Si le titre est court (< 60 caractères), c'est un h2 avec contenu en p
                                if len(title_part) < 60:
                                    content_html += f'<h2>{escape_html_attr(section_num)} {escape_html_attr(title_part)}</h2>\n'
                                    if content_part:
                                        content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(content_part)}</p>\n'
                                else:
                                    # Titre trop long, tout mettre en paragraphe
                                    content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(section_num)} {escape_html_attr(section_text)}</p>\n'
                            elif len(section_text) < 80:
                                # Titre court sans ":"
                                content_html += f'<h2>{escape_html_attr(section_num)} {escape_html_attr(section_text)}</h2>\n'
                            else:
                                # Paragraphe long sans ":"
                                content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(section_num)} {escape_html_attr(section_text)}</p>\n'
                        i += 2
                    else:
                        # Texte normal (pas de numéro de section)
                        text = sections[i].strip()
                        if text:
                            content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(text)}</p>\n'
                        i += 1
            else:
                # Pas de sections numérotées détectées, traiter ligne par ligne
                lines = legal_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Détecter les titres de section (commencent par un chiffre suivi d'un point)
                    if re.match(r'^\d+\.\s+[A-Z]', line):
                        match = re.match(r'^(\d+\.)\s+(.+)$', line)
                        if match:
                            section_num = match.group(1)
                            section_title = match.group(2)
                            if len(section_title) < 80:
                                content_html += f'<h2>{escape_html_attr(section_num)} {escape_html_attr(section_title)}</h2>\n'
                            else:
                                content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(line)}</p>\n'
                        else:
                            content_html += f'<h2>{escape_html_attr(line)}</h2>\n'
                    else:
                        content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(line)}</p>\n'
    content_html += '</section>'
    
    html = re.sub(
        r'<main>.*?</main>',
        f'<main>\n{content_html}\n</main>',
        html,
        flags=re.DOTALL
    )
    
    return html

def main():
    """Fonction principale."""
    print("=" * 70)
    print("📄 GÉNÉRATION ET VÉRIFICATION DES PAGES MENU/FOOTER")
    print("=" * 70)
    
    # 1. Charger les traductions depuis CSV
    print("\n📖 Chargement des traductions depuis translations.csv...")
    translations = load_translations_from_csv()
    if not translations:
        print("❌ Aucune traduction trouvée")
        return False
    
    print(f"✅ {len(translations)} clés chargées")
    
    # 1.5. Charger les produits depuis CSV
    print("\n📦 Chargement des produits depuis all_products.csv...")
    all_products = load_products_from_csv()
    print(f"✅ {len(all_products)} produits chargés")
    
    # 2. Créer les dossiers si nécessaire
    CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    LEGAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # 3. Traiter les pages catégories (menu.*)
    print("\n🔄 Traitement des pages catégories...")
    print("-" * 70)
    
    menu_keys = [k for k in translations.keys() if k.startswith('menu.') and k != 'home.en']
    menu_keys_sorted = sorted(menu_keys)
    
    for index, menu_key in enumerate(menu_keys_sorted, start=1):
        category_name = translations.get(menu_key, '')
        
        if not category_name:
            continue
        
        # Utiliser le numéro comme slug (1, 2, 3, etc.)
        category_number = str(index)
        page_path = CATEGORIES_DIR / f"{category_number}.html"
        
        if page_path.exists():
            print(f"  ✓ {page_path.name} existe - Mise à jour menu/footer/produits depuis CSV...")
            with open(page_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Récupérer menu et footer depuis CSV
            menu_items = get_menu_items_from_csv(translations, page_type='category')
            footer_items = get_footer_items_from_csv(translations, page_type='category')
            
            # Mettre à jour menu et footer
            html_content = update_menu_and_footer_in_page(html_content, menu_items, footer_items, translations)
            
            # Corriger la langue dans le tag html
            lang_code = detect_language_code()
            html_content = re.sub(r'<html lang="[^"]*"', f'<html lang="{lang_code}"', html_content)
            html_content = re.sub(r"<html lang='[^']*'", f'<html lang="{lang_code}"', html_content)
            
            # Mettre à jour le titre, meta description et la description de la catégorie
            category_title = get_translation(f'meta.title.menu.{category_number}', translations, f'{category_name} - AliExpress Affiliate')
            category_description = get_translation(f'meta.des.menu.{category_number}', translations, f'Discover our selection of {category_name}')
            category_content = get_translation(f'descripton.{category_number}', translations, '')
            
            html_content = re.sub(r'<title>.*?</title>', f'<title>{escape_html_attr(category_title)}</title>', html_content)
            html_content = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{escape_html_attr(category_description)}">', html_content)
            html_content = re.sub(r'<h1[^>]*class="section-title"[^>]*>.*?</h1>', f'<h1 class="section-title">{escape_html_attr(category_name)}</h1>', html_content)
            
            # Ajouter ou mettre à jour la description de la catégorie
            if category_content:
                description_html = f'<div class="category-description">\n<p>{escape_html_attr(category_content)}</p>\n</div>'
                # Vérifier si une description existe déjà
                if re.search(r'<div class="category-description">', html_content):
                    # Remplacer la description existante
                    html_content = re.sub(
                        r'<div class="category-description">.*?</div>',
                        description_html,
                        html_content,
                        flags=re.DOTALL
                    )
                else:
                    # Ajouter la description après le h1
                    html_content = re.sub(
                        r'(<h1[^>]*class="section-title"[^>]*>.*?</h1>)',
                        rf'\1\n{description_html}',
                        html_content
                    )
            
            # Mettre à jour les produits - supprimer TOUS les produits existants et les remplacer
            if all_products:
                products_html = generate_products_html_for_category(category_number, all_products, translations)
                
                # Approche : trouver le div products-container, supprimer TOUT jusqu'à la fermeture qui précède </main>
                # On utilise une regex qui capture depuis <div id="products-container jusqu'à </div> qui précède </main>
                # Pattern: depuis products-container jusqu'à </div> suivi de </main> (avec possibilité d'espaces)
                pattern = r'(<div id="products-container" class="products-grid">).*?(</div>\s*</main>)'
                replacement = rf'\1\n{products_html}\n\2'
                
                html_content = re.sub(
                    pattern,
                    replacement,
                    html_content,
                    flags=re.DOTALL
                )
            
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"    ✅ Menu, footer, description et produits mis à jour depuis CSV")
        else:
            print(f"  📝 Génération de {page_path.name}...")
            html = generate_category_page(category_number, category_name, translations, all_products)
            if html:
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"    ✅ Page générée avec produits")
    
    # 4. Traiter les pages légales (footer.link.* sauf home et sitemap)
    print("\n🔄 Traitement des pages légales...")
    print("-" * 70)
    
    footer_keys = [k for k in translations.keys() if k.startswith('footer.link.')]
    for footer_key in sorted(footer_keys):
        if 'home' in footer_key or 'sitemap' in footer_key:
            continue
        
        legal_text = translations.get(footer_key, '')
        if not legal_text:
            continue
        
        slug = slugify(legal_text)
        page_path = LEGAL_DIR / f"{slug}.html"
        
        if page_path.exists():
            print(f"  ✓ {page_path.name} existe - Mise à jour menu/footer/contenu depuis CSV...")
            with open(page_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Récupérer menu et footer depuis CSV
            menu_items = get_menu_items_from_csv(translations, page_type='legal')
            footer_items = get_footer_items_from_csv(translations, page_type='legal')
            
            # Mettre à jour menu et footer
            html_content = update_menu_and_footer_in_page(html_content, menu_items, footer_items, translations)
            
            # Mettre à jour le contenu de la page (titre, description, contenu)
            legal_slug = footer_key.replace('footer.link.', '')
            legal_title = get_translation(f'legal.{legal_slug}.title', translations, f'{legal_text} - AliExpress Affiliate')
            legal_description = get_translation(f'legal.{legal_slug}.meta.description', translations, f'{legal_text}')
            legal_content = get_translation(f'legal.{legal_slug}.content', translations, '')
            
            # Mettre à jour le titre
            html_content = re.sub(r'<title>.*?</title>', f'<title>{escape_html_attr(legal_title)}</title>', html_content)
            
            # Mettre à jour la meta description
            html_content = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{escape_html_attr(legal_description)}">', html_content, flags=re.DOTALL)
            
            # Mettre à jour le contenu (h1 et main) avec la même logique que generate_legal_page
            if legal_content:
                # Utiliser la même fonction de formatage que generate_legal_page
                # Si le contenu contient déjà du HTML (comme about-us), l'utiliser tel quel
                if legal_content.strip().startswith('<'):
                    content_html = f'<section>\n<h1>{escape_html_attr(legal_title)}</h1>\n{legal_content}\n</section>'
                else:
                    # Formater le contenu : détecter les sections numérotées
                    content_html = f'<section>\n<h1>{escape_html_attr(legal_title)}</h1>\n'
                    # Le contenu peut être sur une seule ligne ou plusieurs lignes
                    # D'abord, essayer de diviser par les numéros de section (1., 2., 3., etc.)
                    sections = re.split(r'(\d+\.\s+)', legal_content)
                    
                    # Si on a trouvé des sections, les traiter
                    if len(sections) > 1:
                        i = 0
                        # Traiter le texte avant la première section (s'il existe)
                        if sections[0].strip() and not re.match(r'^\d+\.\s+$', sections[0]):
                            text = sections[0].strip()
                            if text:
                                content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(text)}</p>\n'
                            i = 1
                        
                        while i < len(sections):
                            if re.match(r'^\d+\.\s+$', sections[i]):
                                # C'est un numéro de section
                                section_num = sections[i].strip()
                                section_text = sections[i+1] if i+1 < len(sections) else ''
                                section_text = section_text.strip()
                                
                                if section_text:
                                    # Chercher le premier ":" pour séparer titre et contenu
                                    if ':' in section_text:
                                        parts = section_text.split(':', 1)
                                        title_part = parts[0].strip()
                                        content_part = parts[1].strip() if len(parts) > 1 else ''
                                        
                                        # Si le titre est court (< 60 caractères), c'est un h2 avec contenu en p
                                        if len(title_part) < 60:
                                            content_html += f'<h2>{escape_html_attr(section_num)} {escape_html_attr(title_part)}</h2>\n'
                                            if content_part:
                                                content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(content_part)}</p>\n'
                                        else:
                                            # Titre trop long, tout mettre en paragraphe
                                            content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(section_num)} {escape_html_attr(section_text)}</p>\n'
                                    elif len(section_text) < 80:
                                        # Titre court sans ":"
                                        content_html += f'<h2>{escape_html_attr(section_num)} {escape_html_attr(section_text)}</h2>\n'
                                    else:
                                        # Paragraphe long sans ":"
                                        content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(section_num)} {escape_html_attr(section_text)}</p>\n'
                                i += 2
                            else:
                                # Texte normal (pas de numéro de section)
                                text = sections[i].strip()
                                if text:
                                    content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(text)}</p>\n'
                                i += 1
                    else:
                        # Pas de sections numérotées détectées, traiter ligne par ligne
                        lines = legal_content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Détecter les titres de section (commencent par un chiffre suivi d'un point)
                            if re.match(r'^\d+\.\s+[A-Z]', line):
                                match = re.match(r'^(\d+\.)\s+(.+)$', line)
                                if match:
                                    section_num = match.group(1)
                                    section_title = match.group(2)
                                    if len(section_title) < 80:
                                        content_html += f'<h2>{escape_html_attr(section_num)} {escape_html_attr(section_title)}</h2>\n'
                                    else:
                                        content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(line)}</p>\n'
                                else:
                                    content_html += f'<h2>{escape_html_attr(line)}</h2>\n'
                            else:
                                content_html += f'<p style="margin-bottom: 2rem;">{escape_html_attr(line)}</p>\n'
                    content_html += '</section>'
                
                # Remplacer le contenu entre <section> et </section> (ou <main> et </main>)
                # La page peut utiliser <section> ou <main>
                if re.search(r'<section>', html_content):
                    html_content = re.sub(
                        r'<section>.*?</section>',
                        content_html,
                        html_content,
                        flags=re.DOTALL
                    )
                else:
                    html_content = re.sub(
                        r'<main>.*?</main>',
                        f'<main>\n{content_html}\n</main>',
                        html_content,
                        flags=re.DOTALL
                    )
            
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"    ✅ Menu, footer et contenu mis à jour depuis CSV")
        else:
            print(f"  📝 Génération de {page_path.name}...")
            html = generate_legal_page(footer_key, legal_text, translations)
            if html:
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"    ✅ Page générée")
    
    print("\n" + "=" * 70)
    print("✅ Terminé!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    main()
