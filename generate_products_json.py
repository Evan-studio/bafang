#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère all_products.json avec toutes les données du CSV
Inclut : images multiples, descriptions, meta
"""

import csv
import json
import os
from pathlib import Path

def extract_images(image_paths_str, product_id):
    """Extrait toutes les images et les convertit en chemins relatifs"""
    if not image_paths_str:
        return []
    
    images = image_paths_str.split('|')
    result = []
    
    for img_path in images:
        img_path = img_path.strip()
        if not img_path:
            continue
        
        # Chercher le nom du fichier (image_1.jpg, image_2.jpg, etc.)
        if '/images/' in img_path or '/images-produit/' in img_path:
            # Extraire le nom du fichier
            filename = os.path.basename(img_path)
            # Construire le chemin relatif
            relative_path = f"images/images-produit/{product_id}/{filename}"
            result.append(relative_path)
    
    return result

def generate_all_products_json():
    """Génère le fichier all_products.json"""
    csv_file = Path(__file__).parent / 'all_products.csv'
    
    if not csv_file.exists():
        print(f"❌ Fichier {csv_file} introuvable")
        return False
    
    products = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_id = row.get('product_id', '').strip()
                if not product_id:
                    continue
                
                # Extraire toutes les images
                images = extract_images(row.get('image_paths', ''), product_id)
                
                # Générer le nombre d'avis (même système que pages catégorie)
                import random
                last_6 = int(str(product_id)[-6:]) if product_id else None
                random.seed(last_6)
                reviews_count = random.randint(15, 150)
                random.seed()  # Réinitialiser le seed
                
                product = {
                    'id': product_id,
                    'title': row.get('titre', '') or row.get('name', ''),
                    'name': row.get('name', ''),
                    'affiliate_link': row.get('affiliate_links', ''),
                    'image': images[0] if images else '',
                    'images': images,
                    'description_short': row.get('description_short', ''),
                    'description_long': row.get('description', ''),
                    'description': row.get('description', ''),
                    'meta_title': row.get('meta_title', ''),
                    'meta_description': row.get('meta_description', ''),
                    'price': row.get('price', ''),
                    'reviews_count': reviews_count,
                }
                
                # Ne garder que les produits avec un lien d'affiliation
                if product['affiliate_link']:
                    products.append(product)
        
        # Sauvegarder dans all_products.json
        output_file = Path(__file__).parent / 'all_products.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(products)} produits générés dans {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    generate_all_products_json()


