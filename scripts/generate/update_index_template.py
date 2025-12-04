#!/usr/bin/env python3
"""
Script pour mettre à jour index.html (TEMPLATE) depuis translations.csv

IMPORTANT : Ce script ne modifie JAMAIS la structure HTML.
Il met uniquement à jour le CONTENU textuel depuis le CSV.

Fonctionnalités :
- Lit uniquement translations.csv (colonne 'en')
- Met à jour tous les textes depuis le CSV
- Génère dynamiquement le MENU depuis menu.* du CSV
- Génère dynamiquement le FOOTER depuis footer.link.* du CSV
- Crée automatiquement les slugs pour les liens
- Ne touche JAMAIS à la structure HTML, seulement au contenu

Exemple de slugs :
- menu.test2en → test2en.html
- footer.link.conditions → terms-of-use.html (slug du texte "Terms of Use")

Usage:
    python3 scripts/generate/update_index_template.py
"""

import csv
import re
import unicodedata
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).parent.parent.parent
TRANSLATIONS_CSV = BASE_DIR / 'translations.csv'
INDEX_HTML = BASE_DIR / 'index.html'
PRODUCTS_CSV = BASE_DIR / 'CSV' / 'all_products.csv'

# Détecter si on est dans un dossier de langue (ex: fr/, de/, es/)
# Les dossiers de langue sont en minuscules et ont 2 lettres
def get_home_link():
    """Retourne le lien HOME approprié selon le contexte."""
    base_name = BASE_DIR.name.lower()
    # Si le nom du dossier est une langue (2 lettres), on est dans un dossier de langue
    if len(base_name) == 2 and base_name.isalpha():
        return "./"  # Lien relatif pour rester dans le dossier de langue
    return "/"  # Lien absolu pour la racine

def slugify(text):
    """
    Convertit un texte en slug (minuscules, tirets, sans accents).
    
    Exemples:
        "Test Category" → "test-category"
        "Terms of Use" → "terms-of-use"
        "Découvrez nos Produits!" → "decouvrez-nos-produits"
    """
    if not text:
        return ''
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Supprime caractères spéciaux
    slug = re.sub(r'[-\s]+', '-', slug)   # Remplace espaces/tirets multiples par un tiret
    slug = unicodedata.normalize('NFD', slug)  # Normalise Unicode
    slug = slug.encode('ascii', 'ignore').decode('ascii')  # Supprime accents
    slug = slug.strip('-')  # Nettoie les tirets en début/fin
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

def unescape_html(text):
    """Déséchappe le HTML si nécessaire (pour les données qui viennent de Google Sheets)."""
    if not text:
        return ""
    # Déséchapper les entités HTML courantes
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
    return text

def escape_html_attr(text):
    """Échappe les caractères spéciaux pour les attributs HTML."""
    if not text:
        return ""
    # Si le texte contient déjà du HTML échappé, le déséchapper d'abord
    if '&lt;' in text or '&gt;' in text:
        text = unescape_html(text)
    return escape(text).replace('"', '&quot;')

def load_categories_from_csv(translations):
    """
    Charge les catégories depuis translations.csv.
    Retourne une liste de dict avec : slug, menu_name, slug_url, number
    Utilise des numéros (1, 2, 3...) comme slugs basés sur l'ordre dans le CSV.
    """
    categories = []
    
    # Trouver toutes les clés menu.* (sauf home.en)
    menu_keys = [k for k in translations.keys() if k.startswith('menu.') and k != 'home.en']
    
    # Trier pour avoir un ordre cohérent
    menu_keys_sorted = sorted(menu_keys)
    
    # Assigner un numéro à chaque catégorie (commence à 1)
    for index, menu_key in enumerate(menu_keys_sorted, start=1):
        menu_name = translations.get(menu_key, '')
        
        if not menu_name:
            continue
        
        # Utiliser le numéro comme slug (1, 2, 3, etc.)
        category_number = str(index)
        
        categories.append({
            'slug': category_number,
            'menu_name': menu_name,
            'slug_url': category_number,  # Utiliser le numéro comme slug URL
            'number': category_number
        })
    
    return categories

def load_footer_links_from_csv(translations):
    """
    Charge les liens du footer depuis translations.csv.
    Retourne une liste de dict avec : key, text, slug
    """
    footer_links = []
    
    # Trouver toutes les clés footer.link.*
    footer_keys = [k for k in translations.keys() if k.startswith('footer.link.')]
    
    for footer_key in footer_keys:
        text = translations.get(footer_key, '')
        
        if not text:
            continue
        
        # Créer le slug depuis le texte
        # Exemple: "Terms of Use" → "terms-of-use"
        slug = slugify(text)
        
        footer_links.append({
            'key': footer_key,
            'text': text,
            'slug': slug
        })
    
    # Trier par key pour avoir un ordre cohérent
    footer_links.sort(key=lambda x: x['key'])
    
    return footer_links

def update_meta_tags(html, translations):
    """Met à jour les meta tags (title, description) et le schema.org JSON-LD."""
    site_title = get_translation('site.meta.title', translations, 'AliExpress Affiliate Program - Best Products')
    site_description = get_translation('site.meta.description', translations, 'Discover the best AliExpress products')
    contact_email = get_translation('site.contact.email', translations, 'contact@naturehike-shop.com')
    
    # Mettre à jour le <title>
    html = re.sub(r'<title>.*?</title>', f'<title>{escape_html_attr(site_title)}</title>', html, flags=re.DOTALL)
    
    # Mettre à jour la meta description
    html = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{escape_html_attr(site_description)}">',
        html
    )
    
    # Mettre à jour le schema.org JSON-LD avec l'email depuis CSV
    schema_pattern = r'<script type="application/ld\+json">\s*\{[^}]*"email":\s*"[^"]*"[^}]*\}\s*</script>'
    schema_json = f'{{"@context": "https://schema.org", "@type": "Organization", "name": "Affiliation AliExpress", "url": "https://votresite.com", "contactPoint": {{"@type": "ContactPoint", "email": "{escape_html_attr(contact_email)}", "contactType": "Customer Service"}}}}'
    html = re.sub(
        schema_pattern,
        f'<script type="application/ld+json">\n{schema_json}\n</script>',
        html,
        flags=re.DOTALL
    )
    
    print(f"  ✅ Meta tags et schema.org mis à jour")
    return html

def update_lang_attribute(html):
    """S'assure que la page est en anglais."""
    html = re.sub(r'<html lang="[^"]*"', '<html lang="en"', html)
    print(f"  ✅ Langue mise à jour en anglais")
    return html

def update_menu(html, translations):
    """
    Génère et met à jour le menu depuis translations.csv.
    Le menu est généré dynamiquement depuis menu.* du CSV.
    """
    categories = load_categories_from_csv(translations)
    home_text = get_translation('home.en', translations, 'Home')
    
    # Générer le menu HTML (en majuscule)
    home_link = get_home_link()
    menu_items = [f'<li><a href="{home_link}">{escape_html_attr(home_text.upper())}</a></li>']
    
    for cat in categories:
        # Le slug URL est créé depuis le nom du menu
        # Exemple: menu.test2en → "test2en" → page_html/categories/test2en.html
        page_path = f'page_html/categories/{cat["slug_url"]}.html'
        menu_items.append(f'<li><a href="{page_path}">{escape_html_attr(cat["menu_name"].upper())}</a></li>')
    
    menu_html = '\n'.join(menu_items)
    
    # Remplacer TOUT le contenu du menu (entre <ul class="menu" id="menu"> et </ul>)
    pattern = r'(<ul class="menu" id="menu">).*?(</ul>)'
    replacement = r'\1\n' + menu_html + r'\n\2'
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    print(f"  ✅ Menu mis à jour avec {len(categories)} catégories")
    return html

def update_logo_link(html):
    """
    Corrige le lien du logo pour qu'il reste dans le dossier de langue.
    """
    home_link = get_home_link()
    # Remplacer href="/" dans le logo par le bon lien
    pattern = r'(<a href="/" class="logo" id="logo">)'
    replacement = f'<a href="{home_link}" class="logo" id="logo">'
    html = re.sub(pattern, replacement, html)
    return html

def update_categories_section(html, translations):
    """
    Génère et met à jour la section catégories depuis translations.csv.
    Les catégories sont générées dynamiquement depuis menu.* du CSV.
    """
    categories = load_categories_from_csv(translations)
    
    # Générer les cartes de catégories
    category_cards = []
    for cat in categories:
        category_link = f'page_html/categories/{cat["slug_url"]}.html'
        category_name_escaped = escape_html_attr(cat['menu_name'])
        
        # Image par numéro (1.webp, 2.webp, etc.)
        image_path = f'../images/categories/{cat["number"]}.webp'
        
        card = f'''<a href="{category_link}" class="category-card">
<img src="{image_path}" alt="{category_name_escaped}" class="category-image" loading="lazy" onerror="this.onerror=null;this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'400\' height=\'300\'%3E%3Crect fill=\'%23f5f5f5\' width=\'400\' height=\'300\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' fill=\'%23999\' font-family=\'Arial\' font-size=\'18\'%3E{category_name_escaped}%3C/text%3E%3C/svg%3E'">
<div class="category-info">
<h3 class="category-name">{category_name_escaped}</h3>
</div>
</a>'''
        category_cards.append(card)
    
    categories_html = '\n'.join(category_cards)
    
    # Remplacer TOUTE la section catégories (entre <div class="categories-grid"> et </div></section>)
    pattern = r'(<div class="categories-grid">).*?(</div>\s*</section>)'
    replacement = r'\1\n' + categories_html + r'\n\2'
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    print(f"  ✅ Section catégories mise à jour avec {len(categories)} catégories")
    return html

def update_hero_section(html, translations):
    """Met à jour la section hero depuis le CSV."""
    hero_title = get_translation('homepage.hero.title', translations, '')
    hero_subtitle = get_translation('homepage.hero.subtitle', translations, '')
    hero_button = get_translation('homepage.hero.button', translations, '')
    hero_button_url = get_translation('homepage.hero.button.url', translations, '#produits')  # URL depuis CSV, défaut: #produits
    
    if hero_title:
        html = re.sub(
            r'<h1[^>]*id="hero-title"[^>]*>.*?</h1>',
            f'<h1 id="hero-title">{escape_html_attr(hero_title)}</h1>',
            html,
            flags=re.DOTALL
        )
    
    if hero_subtitle:
        html = re.sub(
            r'<p[^>]*id="hero-subtitle"[^>]*>.*?</p>',
            f'<p id="hero-subtitle">{escape_html_attr(hero_subtitle)}</p>',
            html,
            flags=re.DOTALL
        )
    
    if hero_button:
        # Utiliser l'URL depuis le CSV, ou #produits par défaut
        html = re.sub(
            r'<a[^>]*id="hero-button"[^>]*>.*?</a>',
            f'<a href="{escape_html_attr(hero_button_url)}" class="hero-button" id="hero-button">{escape_html_attr(hero_button)}</a>',
            html,
            flags=re.DOTALL
        )
    
    print(f"  ✅ Section hero mise à jour")
    return html

def update_section_titles(html, translations):
    """Met à jour les titres de sections depuis le CSV."""
    section_titles = {
        'homepage.categories.title': r'<h2[^>]*class="section-title"[^>]*>.*?</h2>',
        'homepage.bestsellers.title': r'<h2[^>]*class="section-title"[^>]*>.*?</h2>',
        'homepage.presentation.title': r'<h2>.*?</h2>',
        'homepage.advantages.title': r'<h2[^>]*>.*?</h2>',
        'homepage.stats.title': r'<h2[^>]*class="section-title"[^>]*>.*?</h2>',
        'homepage.faq.title': r'<h2[^>]*class="section-title"[^>]*>.*?</h2>',
        'homepage.testimonials.title': r'<h2[^>]*class="section-title"[^>]*>.*?</h2>',
    }
    
    # Pour chaque section, trouver et remplacer le titre
    for key, pattern in section_titles.items():
        title = get_translation(key, translations, '')
        if title:
            # Trouver la section et remplacer le titre
            # On cherche dans le contexte de la section
            if 'categories' in key:
                html = re.sub(
                    r'(<section class="categories-section">.*?<h2[^>]*class="section-title"[^>]*>).*?(</h2>)',
                    rf'\1{escape_html_attr(title)}\2',
                    html,
                    flags=re.DOTALL
                )
            elif 'bestsellers' in key:
                html = re.sub(
                    r'(<section id="produits">.*?<h2[^>]*class="section-title"[^>]*>).*?(</h2>)',
                    rf'\1{escape_html_attr(title)}\2',
                    html,
                    flags=re.DOTALL
                )
            elif 'presentation' in key:
                html = re.sub(
                    r'(<section class="presentation">.*?<h2>).*?(</h2>)',
                    rf'\1{escape_html_attr(title)}\2',
                    html,
                    flags=re.DOTALL
                )
            elif 'advantages' in key:
                html = re.sub(
                    r'(<section id="avantages">.*?<h2[^>]*>).*?(</h2>)',
                    rf'\1{escape_html_attr(title)}\2',
                    html,
                    flags=re.DOTALL
                )
            elif 'stats' in key:
                html = re.sub(
                    r'(<section class="stats-section">.*?<h2[^>]*class="section-title"[^>]*>).*?(</h2>)',
                    rf'\1{escape_html_attr(title)}\2',
                    html,
                    flags=re.DOTALL
                )
            elif 'faq' in key:
                html = re.sub(
                    r'(<section class="faq-section">.*?<h2[^>]*class="section-title"[^>]*>).*?(</h2>)',
                    rf'\1{escape_html_attr(title)}\2',
                    html,
                    flags=re.DOTALL
                )
            elif 'testimonials' in key:
                html = re.sub(
                    r'(<section class="testimonials-section">.*?<h2[^>]*class="section-title"[^>]*>).*?(</h2>)',
                    rf'\1{escape_html_attr(title)}\2',
                    html,
                    flags=re.DOTALL
                )
    
    print(f"  ✅ Titres de sections mis à jour")
    return html

def update_presentation_section(html, translations):
    """Met à jour la section présentation depuis le CSV."""
    presentation_content = get_translation('homepage.presentation.content', translations, '')
    
    if presentation_content:
        from html import escape as html_escape
        # Séparer le contenu en paragraphes (par lignes)
        paragraphs = [p.strip() for p in presentation_content.split('\n') if p.strip()]
        if not paragraphs:
            paragraphs = [presentation_content]
        
        # Remplacer tout le contenu entre <div class="presentation-content"> et </div>
        content_html = '\n'
        for para in paragraphs:
            content_html += f'<p>{html_escape(para)}</p>\n'
        
        html = re.sub(
            r'(<div class="presentation-content">\s*<h2>.*?</h2>\s*).*?(\s*</div>)',
            rf'\1{content_html}\2',
            html,
            flags=re.DOTALL
        )
    
    print(f"  ✅ Section présentation mise à jour")
    return html

def update_footer(html, translations):
    """
    Génère et met à jour le footer depuis translations.csv.
    Le footer est généré dynamiquement depuis footer.link.* du CSV.
    Les liens sont créés automatiquement avec les slugs.
    """
    footer_links = load_footer_links_from_csv(translations)
    footer_contact = get_translation('footer.contact', translations, 'Contact us:')
    footer_copyright = get_translation('footer.copyright', translations, '© 2024 AliExpress Affiliate. All rights reserved.')
    contact_email = get_translation('site.contact.email', translations, 'contact@naturehike-shop.com')
    
    # Générer les liens du footer
    footer_links_html = []
    
    # Lien Home
    home_link_obj = next((link for link in footer_links if 'home' in link['key']), None)
    if home_link_obj:
        home_link_href = get_home_link()
        footer_links_html.append(f'<a href="{home_link_href}">{escape_html_attr(home_link_obj["text"])}</a>')
    
    # Lien Sitemap
    sitemap_link = next((link for link in footer_links if 'sitemap' in link['key']), None)
    if sitemap_link:
        footer_links_html.append(f'<a href="sitemap.xml">{escape_html_attr(sitemap_link["text"])}</a>')
    
    # Liens légaux (conditions, mentions, policy)
    # Ces liens pointent vers page_html/legal/{slug}.html
    for link in footer_links:
        if 'home' in link['key'] or 'sitemap' in link['key']:
            continue
        
        # Créer le slug pour le lien
        # Exemple: "Terms of Use" → "terms-of-use"
        slug = link['slug']
        legal_path = f'page_html/legal/{slug}.html'
        
        footer_links_html.append(f'<a href="{legal_path}">{escape_html_attr(link["text"])}</a>')
    
    footer_links_html_str = '\n'.join(footer_links_html)
    
    # Remplacer TOUS les liens du footer (dans <div class="footer-links">)
    html = re.sub(
        r'(<div class="footer-links">).*?(</div>)',
        rf'\1\n{footer_links_html_str}\n\2',
        html,
        flags=re.DOTALL
    )
    
    # Remplacer "Contactez-nous :" / "Contact us:" avec l'email depuis CSV
    html = re.sub(
        r'(<p>)(?:Contactez-nous|Contact us)\s*:\s*<a href="mailto:[^"]+">[^<]+</a></p>',
        rf'<p>{escape_html_attr(footer_contact)} <a href="mailto:{escape_html_attr(contact_email)}">{escape_html_attr(contact_email)}</a></p>',
        html
    )
    
    # Remplacer le copyright
    html = re.sub(
        r'(<p>)&copy;.*?</p>',
        rf'\1{escape_html_attr(footer_copyright)}</p>',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'(<p>)©.*?</p>',
        rf'\1{escape_html_attr(footer_copyright)}</p>',
        html,
        flags=re.DOTALL
    )
    
    print(f"  ✅ Footer mis à jour avec {len(footer_links)} liens")
    return html

def update_advantages_section(html, translations):
    """Met à jour la section avantages depuis le CSV."""
    # Mapping des avantages dans l'ordre exact
    advantages = [
        ('homepage.advantages.factory_price.title', 'homepage.advantages.factory_price.description'),
        ('homepage.advantages.worldwide_shipping.title', 'homepage.advantages.worldwide_shipping.description'),
        ('homepage.advantages.customer_service.title', 'homepage.advantages.customer_service.description'),
        ('homepage.advantages.secure_payment.title', 'homepage.advantages.secure_payment.description'),
    ]
    
    # Remplacer TOUTE la section avantages
    advantages_html = []
    for title_key, desc_key in advantages:
        title = get_translation(title_key, translations, '')
        description = get_translation(desc_key, translations, '')
        
        if title and description:
            advantages_html.append(f'''<div class="feature-card">
<h3>{escape_html_attr(title)}</h3>
<p>{escape_html_attr(description)}</p>
</div>''')
    
    if advantages_html:
        # Remplacer toute la section features
        features_html = '\n'.join(advantages_html)
        html = re.sub(
            r'(<div class="features">\s*).*?(\s*</div>\s*</section>)',
            r'\1' + features_html + r'\2',
            html,
            flags=re.DOTALL
        )
    
    print(f"  ✅ Section avantages mise à jour")
    return html

def update_stats_section(html, translations):
    """Met à jour la section statistiques depuis le CSV."""
    # Mapping des stats dans l'ordre exact
    stats_config = [
        ('homepage.stats.products.number', 'homepage.stats.products.label', '1500+', 'Products Available'),
        ('homepage.stats.countries.number', 'homepage.stats.countries.label', '150+', 'Country of Delivery'),
        ('homepage.stats.satisfaction.number', 'homepage.stats.satisfaction.label', '98%', 'Customer Satisfaction'),
        ('homepage.stats.support.number', 'homepage.stats.support.label', '24/7', 'Customer Service'),
    ]
    
    # Générer toute la section stats depuis le CSV
    stats_html = []
    for number_key, label_key, default_number, default_label in stats_config:
        number = get_translation(number_key, translations, default_number)
        label = get_translation(label_key, translations, default_label)
        
        if number and label:
            stats_html.append(f'''<div class="stat-item">
<div class="stat-number">{escape_html_attr(number)}</div>
<div class="stat-label">{escape_html_attr(label)}</div>
</div>''')
    
    if stats_html:
        # Remplacer toute la section stats-grid
        stats_grid_html = '\n'.join(stats_html)
        html = re.sub(
            r'(<div class="stats-grid">\s*).*?(\s*</div>\s*</section>)',
            r'\1' + stats_grid_html + r'\2',
            html,
            flags=re.DOTALL
        )
    
    print(f"  ✅ Section statistiques mise à jour")
    return html

def update_faq_section(html, translations):
    """Met à jour la section FAQ depuis le CSV."""
    from html import escape as html_escape
    
    # Générer toutes les questions/réponses FAQ depuis le CSV (jusqu'à 10 questions)
    faq_html = []
    for i in range(1, 11):
        question_key = f'homepage.faq.{i}.question'
        answer_key = f'homepage.faq.{i}.answer'
        
        question = get_translation(question_key, translations, '')
        answer = get_translation(answer_key, translations, '')
        
        if question and answer:
            # Nettoyer la réponse (enlever les guillemets)
            answer_clean = answer.strip().strip('"').strip("'")
            
            faq_html.append(f'''<div class="faq-item">
<div class="faq-question" onclick="this.parentElement.classList.toggle('active')">
<span>{html_escape(question)}</span>
<span class="faq-icon">▼</span>
</div>
<div class="faq-answer">
<p>{html_escape(answer_clean)}</p>
</div>
</div>''')
    
    if faq_html:
        # Remplacer toute la section faq-container
        faq_container_html = '\n'.join(faq_html)
        html = re.sub(
            r'(<div class="faq-container">\s*).*?(\s*</div>\s*</section>)',
            r'\1' + faq_container_html + r'\2',
            html,
            flags=re.DOTALL
        )
    
    print(f"  ✅ Section FAQ mise à jour")
    return html

def update_testimonials_section(html, translations):
    """Met à jour la section témoignages depuis le CSV."""
    testimonials_html = ''
    
    # Générer les 4 témoignages depuis le CSV
    for i in range(1, 5):
        name_key = f'homepage.testimonials.{i}.name'
        text_key = f'homepage.testimonials.{i}.text'
        
        name = get_translation(name_key, translations, '')
        text = get_translation(text_key, translations, '')
        
        if name and text:
            from html import escape as html_escape
            # Nettoyer les guillemets du texte
            text_clean = text.strip().strip('"').strip("'")
            
            testimonials_html += f'''<div class="testimonial-card">
<div class="testimonial-header">
<img src="../images/testimonials/client{i}.webp" alt="{html_escape(name)}" class="testimonial-avatar" loading="lazy" onerror="this.onerror=null;this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'60\\' height=\\'60\\'%3E%3Ccircle cx=\\'30\\' cy=\\'30\\' r=\\'30\\' fill=\\'%23e0e0e0\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dy=\\'.3em\\' fill=\\'%23999\\' font-family=\\'Arial\\' font-size=\\'20\\'%3E{html_escape(name[0])}%3C/text%3E%3C/svg%3E'">
<div class="testimonial-info">
<div class="testimonial-name">{html_escape(name)}</div>
<div class="testimonial-stars">★★★★★</div>
</div>
</div>
<p class="testimonial-text">{html_escape(text_clean)}</p>
</div>
'''
    
    if testimonials_html:
        # Remplacer TOUTE la section testimonials-grid
        html = re.sub(
            r'(<div class="testimonials-grid">).*?(</div>\s*</section>)',
            rf'\1\n{testimonials_html}\n\2',
            html,
            flags=re.DOTALL
        )
    
    print(f"  ✅ Section témoignages mise à jour")
    return html

def update_buttons(html, translations):
    """Met à jour les boutons depuis le CSV."""
    # Bouton "View on AliExpress"
    button_text = get_translation('button.view_on_aliexpress', translations, 'View on AliExpress')
    if button_text:
        html = html.replace('Voir sur AliExpress', escape_html_attr(button_text))
        html = html.replace('View on AliExpress', escape_html_attr(button_text))
    
    print(f"  ✅ Boutons mis à jour")
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
            
            # Pour le titre, utiliser titre en priorité (plus court), puis name
            titre_col = get_translated_col('titre')
            name_col = get_translated_col('name')
            description_col = get_translated_col('description')
            description_short_col = get_translated_col('description_short')
            meta_title_col = get_translated_col('meta_title')
            meta_description_col = get_translated_col('meta_description')
            
            def extract_short_title(text):
                """Extrait un titre court depuis un texte qui peut contenir du HTML."""
                if not text:
                    return ''
                # Déséchapper le HTML si nécessaire
                text = unescape_html(text)
                # Extraire seulement le texte (sans HTML)
                import re as re_module
                text_only = re_module.sub(r'<[^>]+>', '', text).strip()
                # Prendre les 100 premiers caractères maximum
                if len(text_only) > 100:
                    text_only = text_only[:100].rsplit(' ', 1)[0] + '...'
                return text_only
            
            for row in reader:
                product_id = row.get('product_id', '').strip()
                if not product_id:
                    continue
                
                # Utiliser titre en priorité (plus court), puis name (mais extraire un titre court)
                titre = row.get(titre_col, '').strip() if titre_col else ''
                name = row.get(name_col, '').strip() if name_col else ''
                
                # TOUJOURS utiliser titre en priorité s'il existe et n'est pas vide
                if titre and titre.strip():
                    title = titre
                elif name:
                    # Si pas de titre, extraire un titre court depuis name (qui peut contenir du HTML)
                    title = extract_short_title(name)
                else:
                    # Fallback : colonnes de base
                    title = row.get('titre', '').strip() or row.get('name', '').strip() or 'Product'
                
                affiliate_link = row.get('affiliate_link', '').strip() or row.get('affiliate_links', '').strip()
                image_paths = row.get('image_paths', '').strip()
                
                products.append({
                    'id': product_id,
                    'title': title,
                    'affiliate_link': affiliate_link,
                    'image_paths': image_paths,
                    'description': row.get(description_col, '').strip() if description_col else '',
                    'description_short': row.get(description_short_col, '').strip() if description_short_col else '',
                    'meta_title': row.get(meta_title_col, '').strip() if meta_title_col else '',
                    'meta_description': row.get(meta_description_col, '').strip() if meta_description_col else '',
                    'price': row.get('price', '').strip() if 'price' in fieldnames else '',
                })
    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture des produits: {e}")
        return products
    
    return products

def extract_first_image_for_homepage(image_paths_str, product_id):
    """Extrait le premier chemin d'image pour la page d'accueil (depuis la racine)."""
    # Nettoyer le product_id (enlever l'apostrophe si présente)
    clean_product_id = str(product_id).strip().lstrip("'")
    
    if not image_paths_str or not product_id:
        return f"../images/products/{clean_product_id}/image_1.jpg"
    
    # Les images sont séparées par |
    images = image_paths_str.split('|')
    if not images:
        return f"../images/products/{clean_product_id}/image_1.jpg"
    
    first_image = images[0].strip()
    
    # Extraire le nom du fichier (image_1.jpg, image_2.jpg, etc.)
    filename = Path(first_image).name
    
    # Utiliser toujours le format standard: ../images/products/{product_id}/{filename}
    return f"../images/products/{clean_product_id}/{filename}"

def update_best_sellers_section(html, translations):
    """Met à jour la section Best Sellers avec les produits depuis all_products.csv."""
    import random
    
    products = load_products_from_csv()
    if not products:
        print(f"  ⚠️  Aucun produit trouvé, section Best Sellers non mise à jour")
        return html
    
    # Sélectionner 5 produits aléatoirement
    random.shuffle(products)
    selected_products = products[:5]
    
    print(f"  📦 {len(selected_products)} produits sélectionnés pour Best Sellers")
    
    # Générer le HTML pour chaque produit
    products_html_list = []
    button_text = get_translation('button.view_on_aliexpress', translations, 'View on AliExpress')
    
    for product in selected_products:
        product_id = product['id']
        title = product['title'] or 'Product'
        affiliate_link = product['affiliate_link'] or '#'
        image_path = extract_first_image_for_homepage(product.get('image_paths', ''), product_id)
        
        # Générer un nombre de reviews aléatoire mais cohérent (basé sur product_id)
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
        
        # Nettoyer le titre : si il contient du HTML, extraire seulement le texte
        import re as re_module
        title_cleaned = unescape_html(title)
        # Si le titre contient du HTML (h3, p, ul, etc.), extraire seulement le texte
        if '<h3>' in title_cleaned or '<p>' in title_cleaned or '<ul>' in title_cleaned:
            # Extraire seulement le texte (sans HTML) et limiter à 100 caractères
            title_text_only = re_module.sub(r'<[^>]+>', '', title_cleaned).strip()
            if len(title_text_only) > 100:
                title_text_only = title_text_only[:100].rsplit(' ', 1)[0] + '...'
            title_for_display = title_text_only
        else:
            title_for_display = title_cleaned
        
        # Pour l'attribut alt, utiliser seulement le texte (sans HTML)
        title_alt_text = re_module.sub(r'<[^>]+>', '', title_cleaned).strip()
        if len(title_alt_text) > 150:
            title_alt_text = title_alt_text[:150].rsplit(' ', 1)[0] + '...'
        title_alt_escaped = escape_html_attr(title_alt_text or title)
        
        # Image avec fallback
        img_tag = f'<img src="{image_path}" alt="{title_alt_escaped}" class="product-image" loading="lazy" onerror="this.onerror=null;this.src=\'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'300\' height=\'300\'%3E%3Crect fill=\'%23f5f5f5\' width=\'300\' height=\'300\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' fill=\'%23999\' font-family=\'Arial\' font-size=\'14\'%3EImage%3C/text%3E%3C/svg%3E\'">'
        
        product_html = f'''<article class="product-card">
<a href="page_html/products/produit-{product_id}.html" style="text-decoration:none;color:inherit">
{img_tag}
<div class="product-info">
<h2 class="product-title">{escape_html_attr(title_for_display)}</h2>
<div class="product-rating">
<span class="product-stars">★★★★★</span>
<span class="product-reviews">({reviews_count})</span>
</div><a href="{affiliate_link}" class="cta-button" target="_blank" rel="noopener noreferrer">{button_text}</a>
</div>
</a>
</article>'''
        
        products_html_list.append(product_html)
    
    products_html = '\n'.join(products_html_list)
    
    # Remplacer la section products-container
    pattern = r'(<div id="products-container" class="products-grid">).*?(</div>\s*</section>)'
    replacement = r'\1\n' + products_html + r'\n\2'
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    print(f"  ✅ Section Best Sellers mise à jour")
    return html

def main():
    """Fonction principale pour mettre à jour index.html depuis translations.csv."""
    print("=" * 70)
    print("📄 MISE À JOUR DE index.html (TEMPLATE) DEPUIS translations.csv")
    print("=" * 70)
    
    # 1. Charger les traductions
    print("\n📖 Chargement des traductions...")
    translations = load_translations_from_csv()
    if not translations:
        print("❌ Aucune traduction trouvée dans translations.csv")
        return False
    
    print(f"✅ {len(translations)} clés de traduction chargées")
    
    # 2. Lire index.html
    print("\n📄 Lecture de index.html...")
    if not INDEX_HTML.exists():
        print(f"❌ Fichier non trouvé: {INDEX_HTML}")
        return False
    
    try:
        with open(INDEX_HTML, 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de index.html: {e}")
        return False
    
    print("✅ index.html chargé")
    
    # 3. Mettre à jour toutes les sections
    print("\n🔄 Mise à jour des sections...")
    print("-" * 70)
    
    html = update_lang_attribute(html)
    html = update_meta_tags(html, translations)
    html = update_logo_link(html)
    html = update_menu(html, translations)
    html = update_categories_section(html, translations)
    html = update_hero_section(html, translations)
    html = update_section_titles(html, translations)
    html = update_presentation_section(html, translations)
    html = update_advantages_section(html, translations)
    html = update_stats_section(html, translations)
    html = update_faq_section(html, translations)
    html = update_testimonials_section(html, translations)
    html = update_best_sellers_section(html, translations)
    html = update_footer(html, translations)
    html = update_buttons(html, translations)
    
    # 4. Sauvegarder
    print("\n💾 Sauvegarde de index.html...")
    try:
        with open(INDEX_HTML, 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ index.html mis à jour avec succès!")
        print("\n" + "=" * 70)
        print("📋 RÉSUMÉ")
        print("=" * 70)
        categories = load_categories_from_csv(translations)
        footer_links = load_footer_links_from_csv(translations)
        print(f"  • Menu : {len(categories)} catégories")
        print(f"  • Footer : {len(footer_links)} liens")
        print(f"  • Langue : Anglais (en)")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

if __name__ == "__main__":
    main()

