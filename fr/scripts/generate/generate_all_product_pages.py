#!/usr/bin/env python3
"""
Script pour générer toutes les pages produit en HTML statique.

Ce script lit les produits depuis all_products.csv et génère une page HTML
statique pour chaque produit, sans JavaScript. Les pages sont générées avec
le menu et footer depuis translations.csv.

Usage:
    python3 scripts/generate/generate_all_product_pages.py
"""

import csv
import re
import random
import unicodedata
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).parent.parent.parent
TRANSLATIONS_CSV = BASE_DIR / 'translations.csv'
PRODUCTS_CSV = BASE_DIR / 'CSV' / 'all_products.csv'
TEMPLATE_PRODUCT = BASE_DIR / 'page_html' / 'templates' / 'produit.html'
PRODUCTS_DIR = BASE_DIR / 'page_html' / 'products'

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

def escape_html_content(text):
    """Échappe les caractères spéciaux pour le contenu HTML (mais préserve le HTML existant)."""
    if not text:
        return ""
    # Ne pas échapper si c'est déjà du HTML valide
    # On laisse le HTML tel quel, mais on échappe les caractères dangereux dans les attributs
    return text

def get_menu_items_from_csv(translations, page_type='product'):
    """
    Lit le CSV et retourne la liste des éléments du menu.
    page_type: 'product' (depuis page_html/products/)
    """
    menu_items = []
    
    # Home (depuis footer.link.home)
    home_text = get_translation('footer.link.home', translations, 'Home')
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
        
        # Depuis page_html/products/, les catégories sont dans ../categories/
        menu_items.append({'text': menu_name, 'url': f"../categories/{category_number}.html"})
    
    return menu_items

def get_footer_items_from_csv(translations, page_type='product'):
    """
    Lit le CSV et retourne la liste des éléments du footer.
    Home est TOUJOURS en premier.
    page_type: 'product' (depuis page_html/products/)
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
            footer_items.append({'text': home_text, 'url': '../../'})
    
    # 2. Sitemap en deuxième
    if sitemap_key:
        sitemap_text = translations.get(sitemap_key, '')
        if sitemap_text:
            footer_items.append({'text': sitemap_text, 'url': '../../sitemap.xml'})
    
    # 3. Pages légales ensuite (triées)
    for footer_key in sorted(legal_keys):
        text = translations.get(footer_key, '')
        if not text:
            continue
        
        slug = slugify(text)
        footer_items.append({'text': text, 'url': f"../legal/{slug}.html"})
    
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
    footer_links_html = []
    for item in footer_items:
        footer_links_html.append(f'<a href="{item["url"]}">{escape_html_attr(item["text"])}</a>')
    
    contact_text = get_translation('footer.contact', translations, 'Contact us:')
    copyright_text = get_translation('footer.copyright', translations, '© 2024 AliExpress Affiliate. All rights reserved.')
    contact_email = get_translation('site.contact.email', translations, 'contact@naturehike-shop.com')
    
    footer_html = f'''<div class="footer-links">
{chr(10).join(footer_links_html)}
</div>
<p>{escape_html_attr(contact_text)} <a href="mailto:{escape_html_attr(contact_email)}">{escape_html_attr(contact_email)}</a></p>
<p>{escape_html_attr(copyright_text)}</p>'''
    
    return footer_html

def extract_images_from_csv(image_paths_str, product_id):
    """Extrait toutes les images depuis le CSV et les convertit en chemins relatifs."""
    if not image_paths_str:
        return []
    
    # Nettoyer le product_id (enlever l'apostrophe si présente)
    clean_product_id = str(product_id).strip().lstrip("'")
    
    images = image_paths_str.split('|')
    result = []
    
    for img_path in images:
        img_path = img_path.strip()
        if not img_path:
            continue
        
        # Extraire le nom du fichier (image_1.jpg, image_2.jpg, etc.)
        filename = Path(img_path).name
        
        # Chemin relatif depuis page_html/products/ vers images/products/
        # Les images sont dans le dossier parent, donc ../../../images/
        relative_path = f"../../../images/products/{clean_product_id}/{filename}"
        result.append(relative_path)
    
    return result if result else [f"../../../images/products/{clean_product_id}/image_1.jpg"]

def get_reviews_count(product_id):
    """Génère le nombre d'avis (même système que pages catégorie)."""
    if not product_id:
        return random.randint(15, 150)
    
    try:
        # Nettoyer le product_id et extraire les 6 derniers chiffres
        clean_id = str(product_id).strip().lstrip("'").replace('.', '').replace('E+', '').replace('e+', '')
        if clean_id and len(clean_id) >= 6:
            last_6 = int(clean_id[-6:])
        else:
            last_6 = None
    except (ValueError, AttributeError):
        last_6 = None
    random.seed(last_6)
    reviews_count = random.randint(15, 150)
    random.seed()  # Réinitialiser le seed
    return reviews_count

def generate_product_page_html(product, translations):
    """Génère le HTML complet d'une page produit."""
    
    # Charger le template
    if not TEMPLATE_PRODUCT.exists():
        print(f"❌ Template non trouvé: {TEMPLATE_PRODUCT}")
        return None
    
    with open(TEMPLATE_PRODUCT, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Récupérer les données du produit
    product_id = product.get('id', '')
    # Utiliser 'name' en priorité, puis 'title', puis 'titre' comme fallback
    name = product.get('name', '') or product.get('title', '') or product.get('titre', '') or 'Product'
    title = name  # Utiliser 'name' comme titre principal
    description_short = product.get('description_short', '')
    description_long = product.get('description') or product.get('description_long', '')
    affiliate_link = product.get('affiliate_link') or product.get('affiliate_links', '')
    price = product.get('price', '')
    meta_title = product.get('meta_title', '') or title
    meta_description = product.get('meta_description', '') or description_short or 'Discover this AliExpress product'
    
    # Extraire les images
    image_paths_str = product.get('image_paths', '')
    images = extract_images_from_csv(image_paths_str, product_id)
    # Nettoyer le product_id (enlever l'apostrophe si présente)
    clean_product_id = str(product_id).strip().lstrip("'")
    main_image = images[0] if images else f"../../../images/products/{clean_product_id}/image_1.jpg"
    
    # Nombre d'avis (même système que pages catégorie)
    reviews_count = get_reviews_count(product_id)
    
    # Menu et footer
    menu_items = get_menu_items_from_csv(translations, page_type='product')
    footer_items = get_footer_items_from_csv(translations, page_type='product')
    menu_html = generate_menu_html(menu_items)
    footer_html = generate_footer_html(footer_items, translations)
    
    # 1. Mettre à jour le lang
    lang_code = detect_language_code()
    html = re.sub(r'<html lang="[^"]*"', f'<html lang="{lang_code}"', html)
    html = re.sub(r"<html lang='[^']*'", f'<html lang="{lang_code}"', html)
    
    # 2. Mettre à jour les meta tags
    html = re.sub(r'<title>.*?</title>', f'<title>{escape_html_attr(meta_title)}</title>', html)
    html = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{escape_html_attr(meta_description)}">', html)
    
    # 3. Mettre à jour le logo (chemin relatif)
    # Le template peut avoir un logo vide ou avec href
    html = re.sub(
        r'<a[^>]*class="logo"[^>]*>.*?</a>',
        f'<a href="../../" class="logo" id="logo"><img src="../../../images/logo/logo.webp" alt="Logo"></a>',
        html,
        flags=re.DOTALL
    )
    
    # 4. Remplacer le menu
    html = re.sub(
        r'<ul class="menu"[^>]*>.*?</ul>',
        f'<ul class="menu" id="menu">\n{menu_html}\n</ul>',
        html,
        flags=re.DOTALL
    )
    
    # Récupérer l'URL YouTube si elle existe
    youtube_url = product.get('youtube_url', '').strip() if product.get('youtube_url') else ''
    has_youtube = bool(youtube_url)
    
    # Extraire l'ID YouTube depuis l'URL
    youtube_id = ''
    if has_youtube:
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\s]+)', youtube_url)
        if match:
            youtube_id = match.group(1)
    
    # 5. Générer le contenu du produit (remplacer le div product-container)
    product_content = f'''<div class="product-header">
<div class="product-images">
<img src="{main_image}" alt="{escape_html_attr(title)}" class="main-image" id="main-image">
'''
    
    # Ajouter la vidéo YouTube si elle existe
    if has_youtube and youtube_id:
        product_content += f'<iframe id="main-video" class="main-video" style="display:none;width:100%;aspect-ratio:1;border:none;border-radius:8px;" src="https://www.youtube.com/embed/{youtube_id}" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" allowfullscreen></iframe>\n'
    
    # Ajouter les miniatures si plusieurs images ou vidéo YouTube
    if len(images) > 1 or has_youtube:
        product_content += '<div class="thumbnails">\n'
        for idx, img in enumerate(images):
            active_class = 'active' if idx == 0 else ''
            product_content += f'<img src="{img}" alt="Image {idx+1}" class="thumbnail {active_class}" onclick="showImage(\'{img}\',event)">\n'
        
        # Ajouter la miniature vidéo si YouTube existe
        if has_youtube:
            product_content += f'<div class="thumbnail-video" onclick="showVideo(event)"><img src="{main_image}" alt="Vidéo"></div>\n'
        
        product_content += '</div>\n'
    
    product_content += '</div>\n'
    product_content += '<div class="product-info">\n'
    product_content += f'<h1>{escape_html_attr(title)}</h1>\n'
    
    if price:
        product_content += f'<div class="product-price">{escape_html_attr(price)}</div>\n'
    
    if description_short:
        # Nettoyer le HTML de description_short (supprimer les h1, h2, etc.)
        desc_clean = description_short
        # Supprimer les balises h1-h6
        desc_clean = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', '', desc_clean, flags=re.DOTALL)
        product_content += f'<div class="description-short">{desc_clean}</div>\n'
    
    # Avis (étoiles + nombre)
    product_content += f'''<div class="product-rating" style="margin:1rem 0;display:flex;align-items:center;gap:0.5rem;">
<span class="product-stars" style="color:#ffc107;font-size:1.2rem;">★★★★★</span>
<span class="product-reviews" style="color:#666;font-size:0.9rem;">({reviews_count})</span>
</div>
'''
    
    if affiliate_link:
        button_text = get_translation('button.view_on_aliexpress', translations, 'View on AliExpress')
        product_content += f'<a href="{escape_html_attr(affiliate_link)}" class="cta-button" target="_blank" rel="noopener noreferrer">{escape_html_attr(button_text)}</a>\n'
    
    product_content += '</div>\n'
    product_content += '</div>\n'
    
    # Description longue
    if description_long:
        # Supprimer les h1, h2, etc. de la description longue
        desc_long_clean = description_long
        desc_long_clean = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', '', desc_long_clean, flags=re.DOTALL)
        if desc_long_clean.strip():
            product_content += f'<div class="description-long">{desc_long_clean}</div>\n'
    
    # Remplacer le contenu product-container (remplacer seulement le contenu intérieur)
    html = re.sub(
        r'<div id="product-container"[^>]*>.*?</div>',
        product_content,
        html,
        flags=re.DOTALL
    )
    
    # 6. Remplacer le footer
    html = re.sub(
        r'<footer>.*?</footer>',
        f'<footer>\n{footer_html}\n</footer>',
        html,
        flags=re.DOTALL
    )
    
    # 7. Ajouter le JavaScript minimal pour les images (showImage)
    js_code = '''<script>
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const menu = document.getElementById('menu');
    if (menuToggle && menu) {
        menuToggle.addEventListener('click', function() {
            menu.classList.toggle('active');
        });
    }
    
    window.showImage = function(imgSrc, evt) {
        const mainImg = document.getElementById('main-image');
        const mainVid = document.getElementById('main-video');
        if (mainImg) {
            mainImg.src = imgSrc;
            mainImg.style.display = 'block';
        }
        if (mainVid) {
            mainVid.style.display = 'none';
        }
        document.querySelectorAll('.thumbnail,.thumbnail-video').forEach(t => t.classList.remove('active'));
        if (evt && evt.target) {
            evt.target.closest('.thumbnail,.thumbnail-video')?.classList.add('active');
        }
    };
    
    window.showVideo = function(evt) {
        const mainImg = document.getElementById('main-image');
        const mainVid = document.getElementById('main-video');
        if (mainImg) {
            mainImg.style.display = 'none';
        }
        if (mainVid) {
            mainVid.style.display = 'block';
        }
        document.querySelectorAll('.thumbnail,.thumbnail-video').forEach(t => t.classList.remove('active'));
        if (evt && evt.target) {
            evt.target.closest('.thumbnail-video')?.classList.add('active');
        }
    };
});
</script>'''
    
    # Remplacer tout le script existant par le nouveau
    html = re.sub(
        r'<script>.*?</script>',
        js_code,
        html,
        flags=re.DOTALL
    )
    
    return html

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
            description_col = get_translated_col('description')
            description_short_col = get_translated_col('description_short')
            meta_title_col = get_translated_col('meta_title')
            meta_description_col = get_translated_col('meta_description')
            
            for row in reader:
                product_id = row.get('product_id', '').strip()
                if not product_id:
                    continue
                
                # Ne garder que les produits avec un lien d'affiliation
                affiliate_link = row.get('affiliate_links', '').strip()
                if not affiliate_link:
                    continue
                
                # Utiliser les colonnes traduites si disponibles
                titre = row.get('titre', '').strip() if 'titre' in fieldnames else ''
                name = row.get(name_col, '').strip() if name_col else ''
                title = name or titre or row.get('name', '').strip() or row.get('titre', '').strip()
                
                # Récupérer youtube_url
                youtube_url = row.get('youtube_url', '').strip() if 'youtube_url' in fieldnames else ''
                
                products.append({
                    'id': product_id,
                    'title': title,
                    'youtube_url': youtube_url,
                    'name': name or row.get('name', '').strip(),
                    'affiliate_link': affiliate_link,
                    'affiliate_links': affiliate_link,
                    'image_paths': row.get('image_paths', '').strip(),
                    'description': row.get(description_col, '').strip() if description_col else row.get('description', '').strip(),
                    'description_short': row.get(description_short_col, '').strip() if description_short_col else row.get('description_short', '').strip(),
                    'meta_title': row.get(meta_title_col, '').strip() if meta_title_col else row.get('meta_title', '').strip(),
                    'meta_description': row.get(meta_description_col, '').strip() if meta_description_col else row.get('meta_description', '').strip(),
                    'price': row.get('price', '').strip() if 'price' in fieldnames else '',
                })
    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture des produits: {e}")
        import traceback
        traceback.print_exc()
        return products
    
    return products

def main():
    """Fonction principale."""
    print("=" * 70)
    print("📦 GÉNÉRATION DE TOUTES LES PAGES PRODUIT (HTML STATIQUE)")
    print("=" * 70)
    
    # 1. Charger les traductions
    print("\n📖 Chargement des traductions depuis translations.csv...")
    translations = load_translations_from_csv()
    if not translations:
        print("❌ Aucune traduction trouvée")
        return False
    
    print(f"✅ {len(translations)} clés chargées")
    
    # 2. Charger les produits
    print("\n📦 Chargement des produits depuis all_products.csv...")
    products = load_products_from_csv()
    if not products:
        print("❌ Aucun produit trouvé")
        return False
    
    print(f"✅ {len(products)} produits chargés")
    
    # 3. Créer le dossier products si nécessaire
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 4. Générer chaque page produit
    print("\n🔄 Génération des pages produit...")
    print("-" * 70)
    
    success_count = 0
    error_count = 0
    
    for product in products:
        product_id = product.get('id', '')
        if not product_id:
            continue
        
        try:
            html = generate_product_page_html(product, translations)
            if html:
                output_file = PRODUCTS_DIR / f"produit-{product_id}.html"
                output_file.write_text(html, encoding='utf-8')
                success_count += 1
                if success_count % 10 == 0:
                    print(f"  ✅ {success_count} pages générées...")
            else:
                error_count += 1
                print(f"  ❌ Erreur pour produit {product_id}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Erreur pour produit {product_id}: {e}")
    
    print("-" * 70)
    print(f"\n✅ {success_count} pages générées avec succès")
    if error_count > 0:
        print(f"⚠️  {error_count} erreurs")
    
    print(f"\n📁 Pages générées dans: {PRODUCTS_DIR}")
    
    # 5. Supprimer les pages orphelines (produits qui ne sont plus dans le CSV)
    print("\n🧹 Nettoyage des pages orphelines...")
    print("-" * 70)
    
    # Récupérer tous les product_id du CSV
    valid_product_ids = {str(p.get('id', '')).strip().lstrip("'") for p in products if p.get('id')}
    
    # Parcourir toutes les pages produits existantes
    orphaned_pages = []
    if PRODUCTS_DIR.exists():
        for page_file in PRODUCTS_DIR.glob('produit-*.html'):
            # Extraire le product_id du nom de fichier
            # Format: produit-{product_id}.html
            try:
                page_product_id = page_file.stem.replace('produit-', '').strip()
                # Nettoyer le product_id (enlever apostrophe si présente)
                clean_page_id = page_product_id.lstrip("'")
                
                if clean_page_id not in valid_product_ids:
                    orphaned_pages.append(page_file)
            except Exception as e:
                print(f"  ⚠️  Erreur lors de l'analyse de {page_file.name}: {e}")
    
    # Supprimer les pages orphelines
    if orphaned_pages:
        print(f"  📋 {len(orphaned_pages)} page(s) orpheline(s) trouvée(s)")
        for page_file in orphaned_pages:
            try:
                page_file.unlink()
                print(f"  🗑️  Supprimé: {page_file.name}")
            except Exception as e:
                print(f"  ⚠️  Erreur lors de la suppression de {page_file.name}: {e}")
        print(f"  ✅ {len(orphaned_pages)} page(s) orpheline(s) supprimée(s)")
    else:
        print("  ✅ Aucune page orpheline trouvée")
    
    print("\n💡 Pour régénérer toutes les pages après modification des produits,")
    print("   relancez simplement ce script.")
    
    return True

if __name__ == '__main__':
    main()

