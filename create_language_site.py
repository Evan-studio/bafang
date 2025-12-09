#!/usr/bin/env python3
"""
Script pour créer un site dans une nouvelle langue à partir d'un site existant.

Ce script :
1. Copie le dossier source (ex: En/, Fr/) vers {code_langue}/
2. Modifie les formules GOOGLETRANSLATE pour la nouvelle langue
3. Modifie les colonnes {source_lang}_auto en {code_langue}_auto
4. Modifie les scripts pour utiliser les bonnes colonnes
5. Modifie lang="{source_lang}" en lang="{code_langue}"
6. Modifie les hreflang et meta tags
"""

import shutil
import re
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent

def find_available_language_dirs():
    """Trouve tous les dossiers de langues disponibles."""
    lang_dirs = []
    for item in BASE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name not in ['APPLI:SCRIPT aliexpress', 'scripts', 'config', 'images', 'page_html', 'upload_cloudflare', 'sauv', 'CSV']:
            # Vérifier si c'est un dossier de langue (contient index.html et translations.csv)
            if (item / 'index.html').exists() and (item / 'translations.csv').exists():
                lang_dirs.append(item)
    return sorted(lang_dirs)

def get_source_language_dir():
    """Retourne automatiquement le dossier racine (toujours en anglais)."""
    # Le dossier racine est toujours la source (en anglais)
    source_dir = BASE_DIR
    
    # Vérifier que le dossier racine contient les fichiers nécessaires
    if not (source_dir / 'index.html').exists():
        print("⚠️  Le dossier racine ne contient pas index.html")
        print("   Le script utilisera quand même le dossier racine comme source")
    
    if not (source_dir / 'translations.csv').exists():
        print("⚠️  Le dossier racine ne contient pas translations.csv")
        print("   Le script utilisera quand même le dossier racine comme source")
    
    return source_dir

def detect_source_language_code(source_dir):
    """Détecte le code de langue source depuis le dossier ou les CSV."""
    # Le dossier racine est toujours en anglais
    if source_dir == BASE_DIR:
        return 'en'
    
    # Essayer depuis le nom du dossier
    dir_name = source_dir.name.lower()
    if len(dir_name) == 2 and dir_name.isalpha():
        return dir_name
    
    # Essayer depuis translations.csv
    translations_csv = source_dir / 'translations.csv'
    if translations_csv.exists():
        try:
            with open(translations_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                if fieldnames:
                    # Chercher une colonne *_auto
                    for col in fieldnames:
                        if col.endswith('_auto'):
                            lang_code = col.replace('_auto', '')
                            if len(lang_code) == 2:
                                return lang_code
        except:
            pass
    
    # Essayer depuis les scripts
    scripts_dir = source_dir / 'scripts' / 'generate'
    if scripts_dir.exists():
        for script_file in scripts_dir.glob('*.py'):
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Chercher lang="xx" ou lang='xx'
                    match = re.search(r'lang=["\']([a-z]{2})["\']', content)
                    if match:
                        return match.group(1)
            except:
                continue
    
    # Par défaut, le dossier racine est en anglais
    return 'en'

def get_target_language_code():
    """Demande le code de langue cible à l'utilisateur."""
    print("=" * 70)
    print("🌍 CRÉATION D'UN SITE DANS UNE NOUVELLE LANGUE")
    print("=" * 70)
    print()
    print("📁 Source: Dossier racine (anglais)")
    print()
    print("Exemples de codes de langue:")
    print("  • de = Allemand")
    print("  • es = Espagnol")
    print("  • it = Italien")
    print("  • pt = Portugais")
    print("  • nl = Néerlandais")
    print("  • fr = Français")
    print()
    
    while True:
        code = input("Entrez le code de langue cible (2 lettres, ex: de, es, fr): ").strip().lower()
        if len(code) == 2 and code.isalpha():
            if code == 'en':
                print("❌ La langue cible ne peut pas être 'en' (c'est la langue source)")
                continue
            return code
        print("❌ Code invalide. Utilisez 2 lettres (ex: de, es, fr)")

def get_language_name(code):
    """Retourne le nom de la langue depuis le code."""
    names = {
        'de': 'Allemand',
        'es': 'Espagnol',
        'it': 'Italien',
        'pt': 'Portugais',
        'nl': 'Néerlandais',
        'ru': 'Russe',
        'pl': 'Polonais',
        'fr': 'Français',
        'en': 'Anglais',
    }
    return names.get(code, code.upper())

def copy_source_to_language(source_dir, target_lang_code):
    """Copie uniquement les fichiers nécessaires du dossier source vers le dossier de langue cible.
    Les images restent dans le dossier parent et sont référencées avec ../images/
    """
    lang_dir = BASE_DIR / target_lang_code.lower()
    
    if lang_dir.exists():
        response = input(f"⚠️  Le dossier {lang_dir.name}/ existe déjà. Le supprimer? (o/n): ")
        if response.lower() == 'o':
            shutil.rmtree(lang_dir)
        else:
            print("❌ Annulé")
            return None
    
    print(f"\n📁 Copie des fichiers nécessaires de {source_dir.name}/ vers {lang_dir.name}/...")
    print(f"   (Les images restent dans le dossier parent)")
    
    # Créer le dossier de langue
    lang_dir.mkdir(parents=True, exist_ok=True)
    
    # Fichiers à copier (fichiers individuels)
    files_to_copy = [
        'index.html',
        '_redirects',
        'robots.txt',
        'sitemap.xml',
        'sitemap.html',
        'translations.csv',
        'custom.css'
    ]
    
    # Dossiers à copier (sans images)
    dirs_to_copy = [
        'CSV',
        'page_html',
        'scripts'
    ]
    
    # Copier les fichiers individuels
    for file_name in files_to_copy:
        source_file = source_dir / file_name
        if source_file.exists():
            target_file = lang_dir / file_name
            shutil.copy2(source_file, target_file)
            print(f"  ✅ {file_name}")
        else:
            print(f"  ⚠️  {file_name} non trouvé")
    
    # Copier les dossiers
    for dir_name in dirs_to_copy:
        source_subdir = source_dir / dir_name
        if source_subdir.exists():
            target_subdir = lang_dir / dir_name
            shutil.copytree(source_subdir, target_subdir)
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ⚠️  {dir_name}/ non trouvé")
    
    print(f"✅ Dossier {lang_dir.name}/ créé (sans images)")
    return lang_dir

def fix_image_paths_in_html(lang_dir):
    """Corrige les chemins des images dans les fichiers HTML pour pointer vers ../images/ au lieu de images/."""
    print(f"\n🖼️  Correction des chemins d'images dans les fichiers HTML...")
    
    # Trouver tous les fichiers HTML
    html_files = []
    html_files.append(lang_dir / 'index.html')
    
    # Ajouter les fichiers HTML dans page_html
    page_html_dir = lang_dir / 'page_html'
    if page_html_dir.exists():
        html_files.extend(page_html_dir.rglob('*.html'))
    
    fixed_count = 0
    for html_file in html_files:
        if not html_file.exists():
            continue
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Calculer le nombre de niveaux de profondeur pour le chemin relatif
            # index.html -> ../images/
            # page_html/categories/1.html -> ../../../images/
            depth = len(html_file.relative_to(lang_dir).parent.parts)
            if depth == 0:
                # index.html est à la racine du dossier de langue
                image_path = '../images/'
            else:
                # Les fichiers dans page_html/ ont besoin de remonter plus haut
                image_path = '../' * (depth + 1) + 'images/'
            
            # Remplacer les chemins images/ par le bon chemin relatif
            # Mais seulement si ce n'est pas déjà un chemin relatif qui commence par ../ ou une URL absolue
            # Ne remplacer que les chemins qui commencent par "images/" (sans ../ avant)
            
            # Corriger les attributs href et src
            content = re.sub(r'(href|src)="images/', rf'\1="{image_path}', content)
            content = re.sub(r"(href|src)='images/", rf"\1='{image_path}", content)
            
            # Corriger les chemins dans les CSS (url(images/...))
            content = re.sub(r'url\(images/', rf'url({image_path}', content)
            content = re.sub(r"url\('images/", rf"url('{image_path}", content)
            content = re.sub(r'url\("images/', rf'url("{image_path}', content)
            
            # Ne pas remplacer les chemins qui commencent déjà par ../ ou http
            
            # Si le contenu a changé, sauvegarder
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                rel_path = html_file.relative_to(lang_dir)
                print(f"  ✅ {rel_path} corrigé")
        
        except Exception as e:
            print(f"  ⚠️  Erreur lors de la correction de {html_file.name}: {e}")
    
    if fixed_count > 0:
        print(f"✅ {fixed_count} fichier(s) HTML corrigé(s) pour les images")
    else:
        print(f"  ℹ️  Aucun fichier HTML à corriger pour les images")

def fix_home_links_in_html(lang_dir):
    """Corrige les liens HOME et logo dans les fichiers HTML pour qu'ils restent dans le dossier de langue."""
    print(f"\n🔗 Correction des liens HOME et logo dans les fichiers HTML...")
    
    # Trouver tous les fichiers HTML
    html_files = []
    html_files.append(lang_dir / 'index.html')
    
    # Ajouter les fichiers HTML dans page_html
    page_html_dir = lang_dir / 'page_html'
    if page_html_dir.exists():
        html_files.extend(page_html_dir.rglob('*.html'))
    
    fixed_count = 0
    for html_file in html_files:
        if not html_file.exists():
            continue
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Corriger le lien du logo : href="/" → href="./"
            content = re.sub(r'(<a href="/" class="logo"[^>]*>)', r'<a href="./" class="logo" id="logo">', content)
            
            # Corriger les liens HOME dans le menu : href="/" → href="./"
            # Mais seulement si c'est dans un contexte de menu (pour éviter de modifier d'autres liens)
            content = re.sub(r'(<li><a href="/">)', r'<li><a href="./">', content)
            
            # Corriger les liens HOME dans le footer : href="/" → href="./"
            # Chercher spécifiquement les liens Home dans le footer
            content = re.sub(r'(<a href="/">Home</a>)', r'<a href="./">Home</a>', content, flags=re.IGNORECASE)
            content = re.sub(r'(<a href="/">HOME</a>)', r'<a href="./">HOME</a>', content)
            
            # Si le contenu a changé, sauvegarder
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                rel_path = html_file.relative_to(lang_dir)
                print(f"  ✅ {rel_path} corrigé")
        
        except Exception as e:
            print(f"  ⚠️  Erreur lors de la correction de {html_file.name}: {e}")
    
    if fixed_count > 0:
        print(f"✅ {fixed_count} fichier(s) HTML corrigé(s)")
    else:
        print(f"  ℹ️  Aucun fichier HTML à corriger")

def update_csv_formulas(lang_dir, source_lang_code, target_lang_code):
    """Modifie les formules GOOGLETRANSLATE dans les CSV."""
    print(f"\n📝 Modification des formules dans les CSV...")
    print(f"   Traduction depuis {source_lang_code} vers {target_lang_code}")
    
    # 1. translations.csv
    translations_csv = lang_dir / 'translations.csv'
    if translations_csv.exists():
        with open(translations_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = list(reader.fieldnames)
        
        # Trouver les colonnes : chercher la colonne source (en, fr, etc.) et la colonne source_auto
        source_col = None
        source_auto_col = None
        target_auto_col = f'{target_lang_code}_auto'
        
        for i, col in enumerate(fieldnames):
            if col == source_lang_code:
                source_col = i
            elif col == f'{source_lang_code}_auto':
                source_auto_col = i
        
        # Si on ne trouve pas la colonne source, chercher 'en' par défaut
        if source_col is None:
            for i, col in enumerate(fieldnames):
                if col == 'en':
                    source_col = i
                    break
        
        # Créer ou modifier la colonne target_auto
        new_fieldnames = list(fieldnames)
        target_col_inserted = False
        if target_auto_col not in new_fieldnames:
            # Créer la nouvelle colonne après la colonne source_auto ou après la colonne source
            if source_auto_col is not None:
                insert_index = source_auto_col + 1
            elif source_col is not None:
                insert_index = source_col + 1
            else:
                insert_index = len(new_fieldnames)
            new_fieldnames.insert(insert_index, target_auto_col)
            target_col_inserted = True
        
        # Calculer la lettre de colonne pour la formule (colonne source)
        # La lettre doit être calculée AVANT l'insertion de la nouvelle colonne
        if source_col is not None:
            source_col_letter = chr(65 + source_col)  # A=0, B=1, etc.
        else:
            # Chercher la colonne 'en' dans les nouveaux fieldnames
            if 'en' in new_fieldnames:
                en_index = new_fieldnames.index('en')
                source_col_letter = chr(65 + en_index)
            else:
                source_col_letter = 'B'  # Par défaut, colonne B
        
        # Modifier les formules pour chaque ligne
        for i, row in enumerate(rows, start=2):  # start=2 car ligne 1 = header
            # Si la colonne target_auto existe déjà, la modifier
            if target_auto_col in row:
                old_value = row.get(target_auto_col, '')
                if old_value.startswith('=GOOGLETRANSLATE'):
                    # Mettre à jour la formule existante
                    new_formula = f'=GOOGLETRANSLATE({source_col_letter}{i};"{source_lang_code}";"{target_lang_code}")'
                    row[target_auto_col] = new_formula
                elif not old_value or not old_value.startswith('='):
                    # Créer une nouvelle formule
                    new_formula = f'=GOOGLETRANSLATE({source_col_letter}{i};"{source_lang_code}";"{target_lang_code}")'
                    row[target_auto_col] = new_formula
            else:
                # Créer la nouvelle colonne avec la formule
                new_formula = f'=GOOGLETRANSLATE({source_col_letter}{i};"{source_lang_code}";"{target_lang_code}")'
                row[target_auto_col] = new_formula
        
        # Si on renomme une colonne source_auto existante
        if source_auto_col is not None and source_auto_col != target_auto_col:
            old_col_name = fieldnames[source_auto_col]
            if old_col_name in new_fieldnames:
                # Remplacer l'ancien nom par le nouveau
                idx = new_fieldnames.index(old_col_name)
                new_fieldnames[idx] = target_auto_col
                # Déplacer les données si nécessaire
                for row in rows:
                    if old_col_name in row:
                        row[target_auto_col] = row.pop(old_col_name)
        
        # Écrire le nouveau fichier
        with open(translations_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  ✅ translations.csv modifié avec colonne {target_auto_col}")
    
    # 2. CSV/all_products.csv
    # IMPORTANT: Utiliser TOUJOURS le fichier ORIGINAL à la racine pour garantir les bons product_id
    # ET garder TOUTES les colonnes de l'original, juste ajouter les colonnes traduites
    original_products_csv = BASE_DIR / 'CSV' / 'all_products.csv'
    products_csv = lang_dir / 'CSV' / 'all_products.csv'
    
    if not original_products_csv.exists():
        print(f"  ⚠️  Fichier original non trouvé: {original_products_csv}")
        return
    
    # Lire depuis l'ORIGINAL (source de vérité pour les product_id)
    print(f"  📖 Lecture depuis le fichier ORIGINAL: CSV/all_products.csv")
    with open(original_products_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames)  # Garder toutes les colonnes originales
    
    # Colonnes de base à traduire
    base_cols = ['titre', 'description', 'name', 'description_short', 'meta_title', 'meta_description']
    
    # Créer le nouveau header : garder TOUTES les colonnes originales
    new_fieldnames = list(fieldnames)
    
    # Pour chaque colonne de base, créer la colonne traduite si elle n'existe pas déjà
    for base_col in base_cols:
        target_col = f'{base_col}_{target_lang_code}_auto'
        
        # Si la colonne traduite n'existe pas déjà, l'ajouter
        if target_col not in new_fieldnames:
            # Chercher où insérer : après la colonne base ou après la dernière colonne _auto de cette base
            insert_idx = None
            
            # Chercher si une colonne _auto existe déjà pour cette base (peu importe la langue)
            for i, col in enumerate(new_fieldnames):
                if col.startswith(f'{base_col}_') and col.endswith('_auto'):
                    # Insérer après la dernière colonne _auto de cette base
                    insert_idx = i + 1
                elif col == base_col and insert_idx is None:
                    # Si pas de colonne _auto trouvée, insérer après la colonne base
                    insert_idx = i + 1
            
            # Si toujours pas trouvé, ajouter à la fin
            if insert_idx is None:
                insert_idx = len(new_fieldnames)
            
            new_fieldnames.insert(insert_idx, target_col)
    
    # Calculer les indices des colonnes source pour les formules
    def get_col_letter(col_name):
        """Retourne la lettre de colonne Excel (A, B, C, ...) pour une colonne donnée."""
        if col_name not in new_fieldnames:
            return None
        idx = new_fieldnames.index(col_name)
        # Excel utilise A-Z puis AA-ZZ, mais on se limite à A-Z pour simplifier
        if idx < 26:
            return chr(65 + idx)
        else:
            # Pour les colonnes au-delà de Z, utiliser AA, AB, etc.
            first_letter = chr(65 + (idx // 26) - 1)
            second_letter = chr(65 + (idx % 26))
            return first_letter + second_letter
    
    # Modifier les formules pour chaque ligne
    for i, row in enumerate(rows, start=2):
        # IMPORTANT: Ajouter apostrophe devant product_id pour forcer le format texte dans Google Sheets
        if 'product_id' in row and row['product_id']:
            product_id = str(row['product_id']).strip()
            if not product_id.startswith("'"):
                row['product_id'] = "'" + product_id
        
        # Pour chaque colonne de base, créer ou mettre à jour la colonne traduite
        for base_col in base_cols:
            target_col = f'{base_col}_{target_lang_code}_auto'
            
            # Initialiser la colonne si elle n'existe pas
            if target_col not in row:
                row[target_col] = ''
            
            # Déterminer la colonne source pour la traduction
            # Priorité : colonne base de la langue source, puis colonne base
            source_col = None
            source_col_name = None
            
            # Chercher d'abord une colonne source_auto
            source_auto_col = f'{base_col}_{source_lang_code}_auto'
            if source_auto_col in fieldnames and row.get(source_auto_col):
                source_col_name = source_auto_col
            # Sinon, utiliser la colonne base
            elif base_col in fieldnames and row.get(base_col):
                source_col_name = base_col
            
            # Créer la formule si on a une colonne source
            if source_col_name:
                source_col_letter = get_col_letter(source_col_name)
                if source_col_letter:
                    # Vérifier si une formule existe déjà
                    old_value = row.get(target_col, '')
                    if old_value.startswith('=GOOGLETRANSLATE'):
                        # Mettre à jour la formule existante
                        new_formula = f'=GOOGLETRANSLATE({source_col_letter}{i};"{source_lang_code}";"{target_lang_code}")'
                        row[target_col] = new_formula
                    elif not old_value or not old_value.startswith('='):
                        # Créer une nouvelle formule
                        new_formula = f'=GOOGLETRANSLATE({source_col_letter}{i};"{source_lang_code}";"{target_lang_code}")'
                        row[target_col] = new_formula
    
    # Écrire le nouveau fichier avec TOUTES les colonnes originales + les nouvelles colonnes traduites
    with open(products_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅ CSV/all_products.csv créé depuis l'original avec TOUTES les colonnes + colonnes traduites")

def update_scripts(lang_dir, source_lang_code, target_lang_code):
    """Modifie les scripts pour utiliser les bonnes colonnes et lang."""
    print(f"\n🔧 Modification des scripts...")
    
    scripts_dir = lang_dir / 'scripts' / 'generate'
    if not scripts_dir.exists():
        print(f"  ⚠️  Dossier scripts non trouvé")
        return
    
    # Trouver tous les scripts Python
    for script_file in scripts_dir.glob('*.py'):
        print(f"  📝 Modification de {script_file.name}...")
        
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer source_lang_code_auto par target_lang_code_auto
        content = re.sub(rf'{re.escape(source_lang_code)}_auto', f'{target_lang_code}_auto', content)
        
        # Remplacer lang="source" par lang="target"
        content = re.sub(rf'lang="{re.escape(source_lang_code)}"', f'lang="{target_lang_code}"', content)
        content = re.sub(rf"lang='{re.escape(source_lang_code)}'", f"lang='{target_lang_code}'", content)
        
        # Remplacer les références à la langue source dans les chemins et URLs
        content = re.sub(rf'/{re.escape(source_lang_code)}/', f'/{target_lang_code}/', content)
        content = re.sub(rf'{re.escape(lang_dir.name)}/', f'{lang_dir.name}/', content)
        
        # Corriger les chemins d'images : ../../images/ -> ../../../images/
        # (car les images sont dans le dossier parent, pas dans le dossier de langue)
        content = re.sub(r'"../../images/', '"../../../images/', content)
        content = re.sub(r"'../../images/", "'../../../images/", content)
        content = re.sub(r'f"../../images/', 'f"../../../images/', content)
        content = re.sub(r"f'../../images/", "f'../../../images/", content)
        
        # Écrire le fichier modifié
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"    ✅ {script_file.name} modifié")

def update_hreflang_in_scripts(lang_dir, source_lang_code, target_lang_code):
    """Modifie les hreflang dans les scripts de génération et les templates."""
    print(f"\n🌐 Modification des hreflang et meta tags...")
    
    scripts_dir = lang_dir / 'scripts' / 'generate'
    
    # Modifier tous les scripts Python
    for script_file in scripts_dir.glob('*.py'):
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer hreflang="source" par hreflang="target"
        content = re.sub(rf'hreflang="{re.escape(source_lang_code)}"', f'hreflang="{target_lang_code}"', content)
        content = re.sub(rf"hreflang='{re.escape(source_lang_code)}'", f"hreflang='{target_lang_code}'", content)
        
        # Remplacer les URLs dans les hreflang (si présentes)
        content = re.sub(rf'href="https://[^"]*/{re.escape(source_lang_code)}/', f'href="https://www.senseofthailand.com/{target_lang_code}/', content)
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ hreflang modifié dans {script_file.name}")
    
    # Modifier aussi index.html si il existe déjà
    index_html = lang_dir / 'index.html'
    if index_html.exists():
        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer hreflang="source"
        content = re.sub(rf'hreflang="{re.escape(source_lang_code)}"', f'hreflang="{target_lang_code}"', content)
        content = re.sub(rf'href="https://[^"]*/{re.escape(source_lang_code)}/', f'href="https://www.senseofthailand.com/{target_lang_code}/', content)
        
        with open(index_html, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ hreflang modifié dans index.html")

def create_generate_script(lang_dir, target_lang_code):
    """Crée le script generate_all_{target_lang_code}.py."""
    lang_name = get_language_name(target_lang_code)
    
    script_content = f'''#!/usr/bin/env python3
"""
Script maître pour générer tout le site en {lang_name} dans le dossier {lang_dir.name}.

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
        print(f"❌ Script non trouvé: {{script_path}}")
        return False
    
    print(f"\\n{{'='*70}}")
    print(f"🚀 Lancement de {{script_name}}")
    print(f"{{'='*70}}\\n")
    
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
        print(f"\\n✅ {{script_name}} terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\\n❌ Erreur lors de l'exécution de {{script_name}}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        print(f"Code de retour: {{e.returncode}}")
        return False
    except Exception as e:
        print(f"\\n❌ Erreur inattendue: {{e}}")
        return False

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🌍 GÉNÉRATION COMPLÈTE DU SITE")
    print("=" * 70)
    print(f"\\n📁 Dossier de travail: {{LANG_DIR}}")
    
    scripts = [
        'update_index_template.py',
        'generate_and_check_menu_footer_pages.py',
        'generate_all_product_pages.py'
    ]
    
    success = True
    for script in scripts:
        if not run_script(script):
            success = False
            print(f"\\n⚠️  Arrêt après l'erreur dans {{script}}")
            break
    
    print("\\n" + "=" * 70)
    if success:
        print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
    else:
        print("❌ GÉNÉRATION TERMINÉE AVEC DES ERREURS")
    print("=" * 70)

if __name__ == '__main__':
    main()
'''
    
    script_path = lang_dir / 'scripts' / f'generate_all_{target_lang_code}.py'
    script_path.write_text(script_content, encoding='utf-8')
    script_path.chmod(0o755)  # Rendre exécutable
    print(f"  ✅ Script generate_all_{target_lang_code}.py créé")

def create_upload_youtube_folder(lang_dir, lang_code):
    """Copie tout le dossier upload youtube pour une langue."""
    print(f"\n📹 Copie du dossier upload youtube pour {lang_code}...")
    
    upload_dir = lang_dir / 'upload youtube'
    
    # Supprimer le dossier s'il existe déjà
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    
    # Copier tout le dossier upload youtube depuis le dossier principal
    source_upload_dir = BASE_DIR / 'upload youtube'
    
    if not source_upload_dir.exists():
        print(f"  ⚠️  Dossier source non trouvé: {source_upload_dir}")
        return None
    
    # Copier tout le contenu du dossier
    shutil.copytree(source_upload_dir, upload_dir)
    print(f"  ✅ Dossier upload youtube copié pour {lang_code}")
    
    # Supprimer les fichiers de tracking et credentials pour que chaque langue ait les siens
    tracking_file = upload_dir / 'upload_tracking.json'
    credentials_file = upload_dir / 'credentials.json'
    config_file = upload_dir / 'upload_config.json'
    
    if tracking_file.exists():
        tracking_file.unlink()
        print(f"  ✅ upload_tracking.json supprimé (sera recréé pour cette langue)")
    
    if credentials_file.exists():
        credentials_file.unlink()
        print(f"  ✅ credentials.json supprimé (sera recréé lors de la première authentification)")
    
    if config_file.exists():
        config_file.unlink()
        print(f"  ✅ upload_config.json supprimé (sera recréé si nécessaire)")
    
    print(f"  ✅ Dossier upload youtube créé pour {lang_code}")
    return upload_dir

def main():
    """Fonction principale."""
    print("\n" + "=" * 70)
    
    # 1. Choisir le dossier source
    source_dir = get_source_language_dir()
    if not source_dir:
        return
    
    # 2. Détecter le code de langue source
    source_lang_code = detect_source_language_code(source_dir)
    if not source_lang_code:
        print(f"⚠️  Impossible de détecter le code de langue source.")
        source_lang_code = input("Entrez le code de langue source (2 lettres, ex: en, fr): ").strip().lower()
        if len(source_lang_code) != 2 or not source_lang_code.isalpha():
            print("❌ Code invalide")
            return
    
    source_lang_name = get_language_name(source_lang_code)
    print(f"✅ Langue source détectée: {source_lang_name} ({source_lang_code})")
    
    # 3. Choisir le code de langue cible
    target_lang_code = get_target_language_code()
    target_lang_name = get_language_name(target_lang_code)
    
    if source_lang_code == target_lang_code:
        print(f"❌ La langue source et la langue cible sont identiques ({source_lang_code})")
        return
    
    print(f"\n🌍 Création du site en {target_lang_name} ({target_lang_code}) depuis {source_lang_name} ({source_lang_code})...")
    print()
    
    # 1. Copier le dossier source vers le dossier cible
    lang_dir = copy_source_to_language(source_dir, target_lang_code)
    if not lang_dir:
        return
    
    # Corriger les chemins d'images dans les fichiers HTML (vers ../images/)
    fix_image_paths_in_html(lang_dir)
    
    # Corriger les liens HOME et logo dans les fichiers HTML
    fix_home_links_in_html(lang_dir)
    
    # 2. Modifier les formules dans les CSV
    update_csv_formulas(lang_dir, source_lang_code, target_lang_code)
    
    # 3. Modifier les scripts
    update_scripts(lang_dir, source_lang_code, target_lang_code)
    
    # 4. Modifier les hreflang
    update_hreflang_in_scripts(lang_dir, source_lang_code, target_lang_code)
    
    # 5. Créer le script maître
    create_generate_script(lang_dir, target_lang_code)
    
    # 6. Créer le dossier upload youtube pour cette langue
    create_upload_youtube_folder(lang_dir, target_lang_code)
    
    print("\n" + "=" * 70)
    print("✅ CRÉATION TERMINÉE!")
    print("=" * 70)
    print(f"\n📁 Dossier créé: {lang_dir.name}/")
    print(f"📝 Formules modifiées: GOOGLETRANSLATE(...,\"{source_lang_code}\";\"{target_lang_code}\")")
    print(f"🔧 Scripts modifiés: {target_lang_code}_auto et lang=\"{target_lang_code}\"")
    print(f"🌐 hreflang modifié: {target_lang_code}")
    print()
    print(f"💡 Pour générer le site:")
    print(f"   cd {lang_dir.name}")
    print(f"   python3 scripts/generate_all_{target_lang_code}.py")
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()

