#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour automatiser l'upload de vidéos YouTube depuis le dossier images
Lit les infos depuis all_products.csv et met à jour le CSV avec les liens YouTube
"""

import os
import sys
import csv
import re
import pandas as pd
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Chemins
BASE_DIR = Path(__file__).parent.parent  # Dossier racine du projet (un niveau au-dessus de upload youtube)
IMAGES_DIR = BASE_DIR / 'images' / 'products'  # Dossier images/products
CSV_FILE = BASE_DIR / 'CSV' / 'all_products.csv'  # CSV dans le dossier CSV
CLIENT_SECRETS_FILE = Path(__file__).parent / 'client_secret_938787798816-u7frdh82p7pckpj8hodtr3i1ss3fcjfu.apps.googleusercontent.com.json'
CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'

# Scopes nécessaires pour uploader des vidéos
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_site_url():
    """Récupère l'URL du site depuis translations.csv."""
    # Chemin vers translations.csv à la racine du projet
    translations_csv = BASE_DIR / 'translations.csv'
    if translations_csv.exists():
        try:
            with open(translations_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('key', '').strip() == 'site.domain':
                        url = row.get('en', '').strip()
                        if url:
                            return url.rstrip('/')
        except Exception as e:
            print(f"⚠️  Erreur lors de la lecture de translations.csv: {e}")
    
    # Fallback
    return "https://uni-ion.com"

def get_authenticated_service():
    """Authentifie l'utilisateur et retourne le service YouTube."""
    credentials = None
    
    # Vérifier si on a déjà des credentials sauvegardés
    if CREDENTIALS_FILE.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(CREDENTIALS_FILE), SCOPES)
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement des credentials: {e}")
            credentials = None
    
    # Si pas de credentials valides, faire le flow OAuth
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            # Essayer de rafraîchir le token
            try:
                credentials.refresh(Request())
            except Exception as e:
                print(f"⚠️  Impossible de rafraîchir le token: {e}")
                credentials = None
        
        if not credentials:
            if not CLIENT_SECRETS_FILE.exists():
                print(f"❌ Fichier client secrets non trouvé: {CLIENT_SECRETS_FILE}")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Sauvegarder les credentials pour la prochaine fois
        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(credentials.to_json())
    
    return build('youtube', 'v3', credentials=credentials)

def find_video_in_folder(folder_path):
    """
    Trouve la première vidéo dans un dossier.
    Retourne le chemin de la vidéo ou None.
    """
    if not folder_path.exists() or not folder_path.is_dir():
        return None
    
    # Extensions vidéo supportées
    video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
    
    videos = []
    for ext in video_extensions:
        videos.extend(list(folder_path.glob(f'*{ext}')))
        videos.extend(list(folder_path.glob(f'*{ext.upper()}')))
    
    if videos:
        # Retourner la première vidéo trouvée
        return videos[0]
    
    return None

def upload_video(youtube, video_file, title, description, privacy_status='private'):
    """
    Upload une vidéo sur YouTube.
    
    Returns:
        L'URL de la vidéo uploadée ou None en cas d'erreur
    """
    if not video_file.exists():
        print(f"❌ Fichier vidéo non trouvé: {video_file}")
        return None
    
    # Préparer les métadonnées de la vidéo
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False  # Non, elle n'est pas conçue pour les enfants
        }
    }
    
    # Créer l'objet MediaFileUpload
    media = MediaFileUpload(
        str(video_file),
        chunksize=-1,
        resumable=True,
        mimetype='video/*'
    )
    
    try:
        print(f"  📤 Upload en cours...")
        
        # Insérer la vidéo
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        # Upload avec reprise automatique en cas d'erreur
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        video_id = response['id']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        print(f"  ✅ Vidéo uploadée: {video_url}")
                        return video_url
                    else:
                        print(f"  ❌ Erreur lors de l'upload: {response}")
                        return None
                else:
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"  📊 Progression: {progress}%", end='\r', flush=True)
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"Erreur {e.resp.status}: {e.content}"
                    retry += 1
                    if retry < 5:
                        print(f"\n  ⚠️  Erreur temporaire, nouvelle tentative ({retry}/5)...")
                        continue
                    else:
                        print(f"\n  ❌ Erreur après {retry} tentatives: {error}")
                        return None
                else:
                    print(f"\n  ❌ Erreur HTTP: {e}")
                    return None
        
        return None
        
    except HttpError as e:
        print(f"  ❌ Erreur HTTP lors de l'upload: {e}")
        if e.resp.status == 403:
            print("  💡 Vérifiez que l'API YouTube Data API v3 est activée dans Google Cloud Console")
        return None
    except Exception as e:
        print(f"  ❌ Erreur lors de l'upload: {e}")
        return None

def clean_text(text):
    """
    Nettoie le texte en enlevant les balises HTML et en limitant la longueur.
    """
    if not text:
        return ""
    
    # Enlever les balises HTML
    text = re.sub(r'<[^>]+>', '', str(text))
    # Enlever les entités HTML
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def build_description(product_id, description_short, site_url):
    """
    Construit la description YouTube avec un lien vers le site au début.
    """
    # Construire l'URL de la page produit
    product_url = f"{site_url}/page_html/products/produit-{product_id}.html"
    
    # Nettoyer la description
    clean_desc = clean_text(description_short)
    
    # Description en anglais avec le lien au début
    description = f"Visit our website for more details: {product_url}\n\n"
    description += clean_desc if clean_desc else "Product details available on our website."
    
    # Limiter à 5000 caractères (limite YouTube)
    if len(description) > 5000:
        description = description[:4997] + "..."
    
    return description

def load_csv_data():
    """Charge les données du CSV."""
    if not CSV_FILE.exists():
        print(f"❌ Fichier CSV non trouvé: {CSV_FILE}")
        return None
    
    try:
        df = pd.read_csv(CSV_FILE)
        return df
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return None

def save_csv_data(df):
    """Sauvegarde les données dans le CSV."""
    try:
        # Créer une sauvegarde
        backup_file = CSV_FILE.with_suffix('.csv.backup_youtube')
        if CSV_FILE.exists():
            import shutil
            shutil.copy2(CSV_FILE, backup_file)
            print(f"💾 Sauvegarde créée: {backup_file}")
        
        # Sauvegarder le CSV
        df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        print(f"✅ CSV mis à jour: {CSV_FILE}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde du CSV: {e}")
        return False

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🚀 SCRIPT D'UPLOAD AUTOMATIQUE YOUTUBE")
    print("=" * 70)
    print()
    
    # Vérifier que les dossiers existent
    if not IMAGES_DIR.exists():
        print(f"❌ Dossier images non trouvé: {IMAGES_DIR}")
        sys.exit(1)
    
    # Charger les données du CSV
    print("📖 Chargement du CSV...")
    df = load_csv_data()
    if df is None:
        sys.exit(1)
    
    # Vérifier si la colonne youtube_url existe, sinon la créer
    if 'youtube_url' not in df.columns:
        df['youtube_url'] = ''
        print("✅ Colonne 'youtube_url' créée dans le CSV")
    
    # Récupérer l'URL du site
    site_url = get_site_url()
    print(f"🌐 URL du site: {site_url}")
    print()
    
    # Authentifier et obtenir le service YouTube
    print("🔐 Authentification YouTube...")
    try:
        youtube = get_authenticated_service()
        print("✅ Authentification réussie")
        print()
    except Exception as e:
        print(f"❌ Erreur lors de l'authentification: {e}")
        sys.exit(1)
    
    # Parcourir les dossiers dans images/
    print("🔍 Recherche des vidéos dans les dossiers...")
    print()
    
    uploaded_count = 0
    skipped_count = 0
    error_count = 0
    
    for product_dir in sorted(IMAGES_DIR.iterdir()):
        if not product_dir.is_dir():
            continue
        
        product_id = str(product_dir.name).strip()
        
        # Vérifier si ce produit existe dans le CSV
        product_row = df[df['product_id'].astype(str) == product_id]
        if product_row.empty:
            print(f"⚠️  Produit {product_id} non trouvé dans le CSV, ignoré")
            continue
        
        # Vérifier si la vidéo est déjà uploadée
        row_index = product_row.index[0]
        if pd.notna(df.at[row_index, 'youtube_url']) and df.at[row_index, 'youtube_url'].strip():
            print(f"⏭️  Produit {product_id}: vidéo déjà uploadée, ignoré")
            skipped_count += 1
            continue
        
        # Chercher la vidéo dans le dossier
        video_file = find_video_in_folder(product_dir)
        if not video_file:
            print(f"ℹ️  Produit {product_id}: aucune vidéo trouvée")
            skipped_count += 1
            continue
        
        print(f"📹 Produit {product_id}: {video_file.name}")
        
        # Récupérer les infos du CSV
        name = str(product_row.iloc[0]['name']).strip() if pd.notna(product_row.iloc[0]['name']) else ''
        description_short = str(product_row.iloc[0]['description_short']).strip() if pd.notna(product_row.iloc[0]['description_short']) else ''
        
        # Nettoyer le titre
        name = clean_text(name)
        
        # Si pas de nom, essayer avec 'titre' comme fallback
        if not name:
            titre = str(product_row.iloc[0]['titre']).strip() if pd.notna(product_row.iloc[0]['titre']) else ''
            name = clean_text(titre)
        
        # Si toujours pas de nom, utiliser le product_id
        if not name:
            name = f"Product {product_id}"
        
        # Limiter le titre à 100 caractères (limite YouTube)
        if len(name) > 100:
            name = name[:97] + "..."
        
        print(f"  📝 Titre: {name[:50]}...")
        
        # Construire la description
        description = build_description(product_id, description_short, site_url)
        
        # Uploader la vidéo
        youtube_url = upload_video(
            youtube,
            video_file,
            name,
            description,
            privacy_status='public'  # 'public', 'private', ou 'unlisted'
        )
        
        if youtube_url:
            # Mettre à jour le CSV
            df.at[row_index, 'youtube_url'] = youtube_url
            uploaded_count += 1
            print()
        else:
            error_count += 1
            print()
    
    # Sauvegarder le CSV
    print("💾 Sauvegarde du CSV...")
    if save_csv_data(df):
        print()
        print("=" * 70)
        print("📊 RÉSUMÉ")
        print("=" * 70)
        print(f"✅ Vidéos uploadées: {uploaded_count}")
        print(f"⏭️  Vidéos ignorées: {skipped_count}")
        print(f"❌ Erreurs: {error_count}")
        print(f"💾 CSV mis à jour avec les liens YouTube")
        print("=" * 70)
    else:
        print("❌ Erreur lors de la sauvegarde du CSV")

if __name__ == '__main__':
    main()

