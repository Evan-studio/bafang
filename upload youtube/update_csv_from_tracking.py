#!/usr/bin/env python3
"""Script pour mettre à jour le CSV avec les URLs YouTube du tracking."""
import json
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CSV_FILE = ROOT_DIR / 'CSV' / 'all_products.csv'
TRACKING_FILE = Path(__file__).parent / 'upload_tracking.json'

if not TRACKING_FILE.exists():
    print("❌ Fichier de tracking non trouvé")
    exit(1)

if not CSV_FILE.exists():
    print("❌ Fichier CSV non trouvé")
    exit(1)

# Charger le tracking
with open(TRACKING_FILE, 'r') as f:
    tracking_data = json.load(f)

uploads = tracking_data.get('uploads', {})
print(f"📊 {len(uploads)} uploads trouvés dans le tracking")

# Charger le CSV
df = pd.read_csv(CSV_FILE)

# S'assurer que la colonne youtube_url existe
if 'youtube_url' not in df.columns:
    df['youtube_url'] = ''

# Convertir en string
df['youtube_url'] = df['youtube_url'].fillna('').astype(str)

# Mettre à jour avec les URLs du tracking (pour la langue 'en' - principal)
updated = 0
for key, val in uploads.items():
    if val['lang'] == 'en':  # Seulement pour le dossier principal
        product_id = str(val['product_id'])
        youtube_url = val['youtube_url']
        
        # Trouver le produit dans le CSV
        product_mask = df['product_id'].astype(str) == product_id
        if product_mask.any():
            current_url = df.loc[product_mask, 'youtube_url'].iloc[0] if product_mask.any() else ''
            if current_url != youtube_url:
                df.loc[product_mask, 'youtube_url'] = youtube_url
                updated += 1
                print(f"✅ Mis à jour: {product_id} -> {youtube_url}")

if updated > 0:
    # Sauvegarder
    df.to_csv(CSV_FILE, index=False, encoding='utf-8')
    print(f"\n✅ {updated} URLs mises à jour dans le CSV")
else:
    print("\nℹ️  Aucune mise à jour nécessaire")

