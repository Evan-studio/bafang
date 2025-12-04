#!/usr/bin/env python3
"""
Script utilitaire pour obtenir les informations d'une catégorie à partir de son category_id
Utilise config/categories.json comme source de mapping
"""

import json
import os

def load_categories():
    """Charge le fichier de mapping des catégories."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config',
        'categories.json'
    )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('categories', [])
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {config_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
        return []

def get_category_by_id(category_id):
    """Retourne les informations d'une catégorie par son ID."""
    categories = load_categories()
    for cat in categories:
        if cat.get('id') == category_id:
            return cat
    return None

def get_category_by_slug(slug):
    """Retourne les informations d'une catégorie par son slug."""
    categories = load_categories()
    for cat in categories:
        if cat.get('slug') == slug:
            return cat
    return None

def get_all_categories():
    """Retourne toutes les catégories triées par menu_order."""
    categories = load_categories()
    return sorted(categories, key=lambda x: x.get('menu_order', 999))

if __name__ == "__main__":
    # Test
    print("📋 Test du système de mapping des catégories\n")
    
    # Afficher toutes les catégories
    all_cats = get_all_categories()
    print(f"✅ {len(all_cats)} catégories trouvées:\n")
    
    for cat in all_cats:
        print(f"  ID: {cat['id']} | Slug: {cat['slug']} | Nom: {cat['name']}")
        print(f"    Page: {cat['page']} | Image: {cat['image']}")
        print()
    
    # Test par ID
    print("\n🔍 Test par category_id:")
    cat_3 = get_category_by_id(3)
    if cat_3:
        print(f"  category_id=3 → {cat_3['name']} ({cat_3['slug']})")
    
    # Test par slug
    print("\n🔍 Test par slug:")
    cat_couchage = get_category_by_slug('couchage')
    if cat_couchage:
        print(f"  slug='couchage' → ID: {cat_couchage['id']}, Nom: {cat_couchage['name']}")



