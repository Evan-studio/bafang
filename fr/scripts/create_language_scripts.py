#!/usr/bin/env python3
"""
Script pour créer les scripts de génération pour une langue spécifique
Copie les templates et adapte les chemins pour la langue
"""

import sys
from pathlib import Path
import shutil

# Le script est dans scripts/, donc BASE_DIR est la racine du projet
BASE_DIR = Path(__file__).parent.parent.parent
TEMPLATES_DIR = BASE_DIR / 'scripts' / 'templates'
MULTILINGUAL_SCRIPTS = BASE_DIR / 'scripts' / 'generate'

LANGUAGES = {
    'fr': 'Français',
    'es': 'Espagnol',
    'de': 'Allemand',
    'it': 'Italien',
    'pt': 'Portugais'
}

def create_language_scripts(lang_code):
    """Crée les scripts de génération pour une langue."""
    if lang_code not in LANGUAGES:
        print(f"❌ Langue non supportée: {lang_code}")
        print(f"Langues disponibles: {', '.join(LANGUAGES.keys())}")
        return False
    
    lang_name = LANGUAGES[lang_code]
    lang_dir = BASE_DIR / lang_code
    scripts_dir = lang_dir / 'scripts' / 'generate'
    
    # Créer la structure de dossiers
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Création des scripts pour {lang_name} ({lang_code})")
    print(f"   Dossier: {scripts_dir}")
    
    # Créer les scripts individuels
    scripts_to_create = [
        ('generate_index_multilingual.py', 'generate_index.py'),
        ('generate_category_pages_multilingual.py', 'generate_category_pages.py'),
        ('generate_products_multilingual.py', 'generate_products.py'),
        ('generate_legal_pages_multilingual.py', 'generate_legal_pages.py'),
    ]
    
    for source, target in scripts_to_create:
        source_path = MULTILINGUAL_SCRIPTS / source
        target_path = scripts_dir / target
        
        if source_path.exists():
            # Lire le script source
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Adapter BASE_DIR pour pointer vers le dossier de la langue
            # Remplacer BASE_DIR = Path(__file__).parent.parent.parent
            # par BASE_DIR = Path(__file__).parent.parent.parent (dossier langue)
            # et ROOT_DIR = BASE_DIR.parent (racine du projet)
            
            # Ajouter ROOT_DIR au début
            if 'ROOT_DIR' not in content:
                content = content.replace(
                    'BASE_DIR = Path(__file__).parent.parent.parent',
                    '''BASE_DIR = Path(__file__).parent.parent.parent  # Dossier de la langue
ROOT_DIR = BASE_DIR.parent  # Racine du projet'''
                )
            
            # Adapter les chemins pour utiliser ROOT_DIR pour les fichiers communs
            content = content.replace(
                'BASE_DIR / \'CSV\'',
                'ROOT_DIR / \'CSV\''
            )
            content = content.replace(
                'BASE_DIR / \'config\'',
                'ROOT_DIR / \'config\''
            )
            content = content.replace(
                'BASE_DIR / \'images\'',
                'ROOT_DIR / \'images\''
            )
            content = content.replace(
                'BASE_DIR / \'translations.csv\'',
                'ROOT_DIR / \'translations.csv\''
            )
            content = content.replace(
                'BASE_DIR / \'CSV\' / \'products_translations.csv\'',
                'ROOT_DIR / \'CSV\' / \'products_translations.csv\''
            )
            
            # Adapter les chemins de templates pour utiliser ROOT_DIR
            content = content.replace(
                'BASE_DIR / \'page_html\' / \'templates\'',
                'ROOT_DIR / \'page_html\' / \'templates\''
            )
            
            # Écrire le script adapté
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ {target} créé")
        else:
            print(f"  ⚠️  {source} non trouvé")
    
    # Créer le script principal generate_site.py
    main_script = scripts_dir / 'generate_site.py'
    template_path = TEMPLATES_DIR / 'generate_language_site.py.template'
    
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Remplacer les placeholders
        template_content = template_content.replace('{{LANG_CODE}}', lang_code)
        template_content = template_content.replace('{{LANG_NAME}}', lang_name)
        
        with open(main_script, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"  ✅ generate_site.py créé")
    else:
        print(f"  ⚠️  Template non trouvé: {template_path}")
    
    # Créer template_utils.py (copie avec adaptations)
    template_utils_source = MULTILINGUAL_SCRIPTS / 'template_utils.py'
    template_utils_target = scripts_dir / 'template_utils.py'
    
    if template_utils_source.exists():
        with open(template_utils_source, 'r', encoding='utf-8') as f:
            utils_content = f.read()
        
        # Adapter les chemins
        utils_content = utils_content.replace(
            'BASE_DIR = Path(__file__).parent.parent.parent',
            '''BASE_DIR = Path(__file__).parent.parent.parent  # Dossier de la langue
ROOT_DIR = BASE_DIR.parent  # Racine du projet'''
        )
        utils_content = utils_content.replace(
            'BASE_DIR / \'config.json\'',
            'ROOT_DIR / \'config.json\''
        )
        utils_content = utils_content.replace(
            'BASE_DIR / \'translations.csv\'',
            'ROOT_DIR / \'translations.csv\''
        )
        utils_content = utils_content.replace(
            'BASE_DIR / \'page_html\' / \'templates\'',
            'ROOT_DIR / \'page_html\' / \'templates\''
        )
        
        with open(template_utils_target, 'w', encoding='utf-8') as f:
            f.write(utils_content)
        
        print(f"  ✅ template_utils.py créé")
    
    # Créer generate_menu.py (copie simple)
    generate_menu_source = MULTILINGUAL_SCRIPTS / 'generate_menu.py'
    generate_menu_target = scripts_dir / 'generate_menu.py'
    
    if generate_menu_source.exists():
        with open(generate_menu_source, 'r', encoding='utf-8') as f:
            menu_content = f.read()
        
        # Adapter les chemins
        menu_content = menu_content.replace(
            'BASE_DIR = Path(__file__).parent.parent.parent',
            '''BASE_DIR = Path(__file__).parent.parent.parent  # Dossier de la langue
ROOT_DIR = BASE_DIR.parent  # Racine du projet'''
        )
        menu_content = menu_content.replace(
            'BASE_DIR / \'config\' / \'categories.json\'',
            'ROOT_DIR / \'config\' / \'categories.json\''
        )
        menu_content = menu_content.replace(
            'BASE_DIR / \'index.html\'',
            'ROOT_DIR / \'index.html\''
        )
        
        with open(generate_menu_target, 'w', encoding='utf-8') as f:
            f.write(menu_content)
        
        print(f"  ✅ generate_menu.py créé")
    
    print(f"\n✅ Scripts créés pour {lang_name} ({lang_code})")
    print(f"   Utilisez: cd {lang_code} && python3 scripts/generate/generate_site.py")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/create_language_scripts.py <lang_code>")
        print(f"Langues disponibles: {', '.join(LANGUAGES.keys())}")
        sys.exit(1)
    
    lang_code = sys.argv[1].lower()
    create_language_scripts(lang_code)

