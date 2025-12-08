#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour automatiser l'upload de vidéos YouTube multilingue avec gestion du quota quotidien.
- Lit les CSV de chaque langue pour les métadonnées traduites
- Utilise toujours les vidéos du dossier principal images/products
- Gère le quota YouTube (6 vidéos/jour par compte)
- Continue automatiquement les jours suivants jusqu'à ce que toutes les vidéos soient uploadées
- Track les uploads par langue et par jour dans un fichier JSON
"""

import os
import sys
import csv
import re
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Chemins
ROOT_DIR = Path(__file__).parent.parent  # Dossier racine du projet
IMAGES_DIR = ROOT_DIR / 'images' / 'products'  # Dossier images/products (commun à toutes les langues)
CLIENT_SECRETS_FILE = Path(__file__).parent / 'client_secret_938787798816-u7frdh82p7pckpj8hodtr3i1ss3fcjfu.apps.googleusercontent.com.json'
CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'
TRACKING_FILE = Path(__file__).parent / 'upload_tracking.json'  # Fichier de suivi des uploads
CONFIG_FILE = Path(__file__).parent / 'upload_config.json'  # Fichier de configuration des langues

# Scopes nécessaires pour uploader des vidéos
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Quota YouTube par jour (peut être modifié via variable d'environnement YOUTUBE_DAILY_QUOTA)
# Par défaut: pas de limite (None)
# Pour définir une limite, exportez: export YOUTUBE_DAILY_QUOTA=10
DAILY_QUOTA = None
if 'YOUTUBE_DAILY_QUOTA' in os.environ:
    try:
        quota = int(os.environ.get('YOUTUBE_DAILY_QUOTA', '0'))
        if quota > 0:
            DAILY_QUOTA = quota
    except ValueError:
        pass

def get_language_dirs():
    """Trouve tous les dossiers de langues disponibles, y compris le dossier principal."""
    lang_dirs = []
    
    # Ajouter le dossier principal (racine) s'il contient CSV/all_products.csv
    main_csv = ROOT_DIR / 'CSV' / 'all_products.csv'
    if main_csv.exists():
        lang_dirs.append(ROOT_DIR)  # Le dossier principal
    
    # Chercher les dossiers de langues
    for item in ROOT_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name not in [
            'APPLI:SCRIPT aliexpress', 'scripts', 'config', 'images', 'page_html', 
            'upload youtube', 'sauv', 'CSV', '__pycache__'
        ]:
            # Vérifier si c'est un dossier de langue (contient CSV/all_products.csv)
            csv_file = item / 'CSV' / 'all_products.csv'
            if csv_file.exists():
                lang_dirs.append(item)
    
    return sorted(lang_dirs, key=lambda x: (x != ROOT_DIR, x.name))  # Principal en premier

def load_config():
    """Charge la configuration depuis le fichier config."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('languages', [])  # Liste des langues à traiter
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de la config: {e}")
    return None

def save_config(languages):
    """Sauvegarde la configuration."""
    config = {
        'languages': languages if languages else []
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de la config: {e}")
        return False

def filter_language_dirs(lang_dirs, selected_languages):
    """Filtre les dossiers de langues selon la sélection."""
    if not selected_languages:
        return lang_dirs  # Toutes les langues
    
    # Normaliser les codes de langues (minuscules)
    selected_languages = [lang.lower() for lang in selected_languages]
    
    filtered = []
    for lang_dir in lang_dirs:
        if lang_dir.name.lower() in selected_languages:
            filtered.append(lang_dir)
    
    return filtered

def get_site_url(lang_dir):
    """Récupère l'URL du site depuis translations.csv d'une langue."""
    # Si c'est le dossier principal, chercher translations.csv à la racine
    translations_csv = lang_dir / 'translations.csv'
    if translations_csv.exists():
        try:
            with open(translations_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('key', '').strip() == 'site.domain':
                        url = row.get('en', '').strip() or row.get(list(row.keys())[1], '').strip()
                        if url:
                            return url.rstrip('/')
        except Exception as e:
            print(f"⚠️  Erreur lors de la lecture de translations.csv: {e}")
    
    # Fallback
    return "https://bafang-shop.com"

def get_lang_code_from_dir(lang_dir):
    """Retourne le code de langue depuis le dossier."""
    if lang_dir == ROOT_DIR:
        return 'en'  # Le dossier principal est en anglais par défaut
    return lang_dir.name

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
    """Trouve la première vidéo dans un dossier."""
    if not folder_path.exists() or not folder_path.is_dir():
        return None
    
    video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
    videos = []
    for ext in video_extensions:
        videos.extend(list(folder_path.glob(f'*{ext}')))
        videos.extend(list(folder_path.glob(f'*{ext.upper()}')))
    
    if videos:
        return videos[0]
    return None

def clean_text(text):
    """Nettoie le texte en enlevant les balises HTML et en limitant la longueur."""
    if not text:
        return ""
    
    text = re.sub(r'<[^>]+>', '', str(text))
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_description(product_id, description_short, site_url, lang_code):
    """Construit la description YouTube avec un lien vers le site."""
    # Construire l'URL de la page produit (adaptée à la langue)
    if lang_code == 'en' or lang_code == '':
        product_url = f"{site_url}/page_html/products/produit-{product_id}.html"
    else:
        product_url = f"{site_url}/{lang_code}/page_html/products/produit-{product_id}.html"
    
    clean_desc = clean_text(description_short)
    
    # Description avec le lien au début
    description = f"Visit our website for more details: {product_url}\n\n"
    description += clean_desc if clean_desc else "Product details available on our website."
    
    # Limiter à 5000 caractères (limite YouTube)
    if len(description) > 5000:
        description = description[:4997] + "..."
    
    return description

def load_tracking():
    """Charge le fichier de tracking des uploads."""
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement du tracking: {e}")
            return {}
    return {}

def save_tracking(tracking_data):
    """Sauvegarde le fichier de tracking."""
    try:
        with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
            json.dump(tracking_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde du tracking: {e}")
        return False

def get_uploads_today(tracking_data):
    """Retourne le nombre d'uploads effectués aujourd'hui."""
    today = date.today().isoformat()
    return tracking_data.get('daily_uploads', {}).get(today, 0)

def can_upload_today(tracking_data):
    """Vérifie si on peut encore uploader aujourd'hui."""
    if DAILY_QUOTA is None:
        return True  # Pas de limite
    uploads_today = get_uploads_today(tracking_data)
    return uploads_today < DAILY_QUOTA

def record_upload(tracking_data, lang_code, product_id, youtube_url):
    """Enregistre un upload dans le tracking."""
    today = date.today().isoformat()
    
    # Initialiser les structures si nécessaire
    if 'daily_uploads' not in tracking_data:
        tracking_data['daily_uploads'] = {}
    if 'uploads' not in tracking_data:
        tracking_data['uploads'] = {}
    
    # Incrémenter le compteur du jour
    tracking_data['daily_uploads'][today] = tracking_data['daily_uploads'].get(today, 0) + 1
    
    # Enregistrer l'upload par langue et produit
    lang_key = f"{lang_code}_{product_id}"
    tracking_data['uploads'][lang_key] = {
        'lang': lang_code,
        'product_id': product_id,
        'youtube_url': youtube_url,
        'upload_date': today,
        'upload_datetime': datetime.now().isoformat()
    }

def is_already_uploaded(tracking_data, lang_code, product_id):
    """Vérifie si une vidéo a déjà été uploadée pour cette langue."""
    lang_key = f"{lang_code}_{product_id}"
    return lang_key in tracking_data.get('uploads', {})

def check_remaining_videos(tracking_data, lang_dirs=None):
    """Compte le nombre de vidéos restantes à uploader."""
    if lang_dirs is None:
        lang_dirs = get_language_dirs()
    
    total_remaining = 0
    
    for lang_dir in lang_dirs:
        lang_code = get_lang_code_from_dir(lang_dir)
        df = load_csv_data(lang_dir)
        if df is None:
            continue
        
        # Chercher la colonne ID
        id_col = 'id' if 'id' in df.columns else 'product_id'
        if id_col not in df.columns:
            continue
        
        for _, row in df.iterrows():
            product_id = str(row.get(id_col, ''))
            if not product_id:
                continue
            
            if not is_already_uploaded(tracking_data, lang_code, product_id):
                product_folder = IMAGES_DIR / product_id
                if find_video_in_folder(product_folder):
                    total_remaining += 1
    
    return total_remaining

def upload_video(youtube, video_file, title, description, privacy_status='public'):
    """Upload une vidéo sur YouTube."""
    if not video_file.exists():
        print(f"❌ Fichier vidéo non trouvé: {video_file}")
        return None
    
    body = {
        'snippet': {
            'title': title[:100] if len(title) > 100 else title,  # Limite YouTube: 100 caractères
            'description': description[:5000] if len(description) > 5000 else description,  # Limite YouTube: 5000 caractères
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(
        str(video_file),
        chunksize=-1,
        resumable=True,
        mimetype='video/*'
    )
    
    try:
        print(f"  📤 Upload en cours...")
        
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
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
        return None
    except Exception as e:
        print(f"  ❌ Erreur lors de l'upload: {e}")
        return None

def load_csv_data(lang_dir):
    """Charge les données du CSV d'une langue."""
    # Si c'est le dossier principal, chercher CSV/all_products.csv à la racine
    csv_file = lang_dir / 'CSV' / 'all_products.csv'
    if not csv_file.exists():
        return None
    
    try:
        df = pd.read_csv(csv_file)
        return df
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return None

def save_csv_data(lang_dir, df):
    """Sauvegarde les données dans le CSV d'une langue."""
    csv_file = lang_dir / 'CSV' / 'all_products.csv'
    try:
        # Créer une sauvegarde
        backup_file = csv_file.with_suffix('.csv.backup_youtube')
        if csv_file.exists():
            import shutil
            shutil.copy2(csv_file, backup_file)
        
        # S'assurer que youtube_url est bien de type string
        if 'youtube_url' in df.columns:
            df['youtube_url'] = df['youtube_url'].fillna('').astype(str)
            # Remplacer 'nan' par chaîne vide
            df['youtube_url'] = df['youtube_url'].replace('nan', '')
        
        df.to_csv(csv_file, index=False, encoding='utf-8')
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde du CSV: {e}")
        return False

def get_product_metadata(df, product_id, lang_code):
    """Récupère les métadonnées d'un produit depuis le CSV."""
    # Chercher la colonne ID (peut être 'id' ou 'product_id')
    id_col = 'id' if 'id' in df.columns else 'product_id'
    
    # Convertir product_id pour la comparaison (essayer int d'abord, puis string)
    try:
        product_id_int = int(product_id)
        product_row = df[df[id_col] == product_id_int]
    except (ValueError, TypeError):
        product_id_str = str(product_id)
        product_row = df[df[id_col].astype(str) == product_id_str]
    
    if product_row.empty:
        # Essayer avec string si int a échoué
        if 'product_id_int' in locals():
            product_id_str = str(product_id)
            product_row = df[df[id_col].astype(str) == product_id_str]
    
    if product_row.empty:
        return None, None
    
    row = product_row.iloc[0]
    
    # Chercher le titre dans la colonne appropriée
    # Priorité: titre_{lang_code} > titre > name_{lang_code} > name
    title_col = None
    if f'titre_{lang_code}' in df.columns:
        title_col = f'titre_{lang_code}'
    elif 'titre' in df.columns:
        title_col = 'titre'
    elif f'name_{lang_code}' in df.columns:
        title_col = f'name_{lang_code}'
    elif 'name' in df.columns:
        title_col = 'name'
    
    if not title_col:
        return None, None
    
    # Chercher la description dans la colonne appropriée
    # Priorité: description_short_{lang_code} > description_short > description_{lang_code} > description
    desc_col = None
    if f'description_short_{lang_code}' in df.columns:
        desc_col = f'description_short_{lang_code}'
    elif 'description_short' in df.columns:
        desc_col = 'description_short'
    elif f'description_{lang_code}' in df.columns:
        desc_col = f'description_{lang_code}'
    elif 'description' in df.columns:
        desc_col = 'description'
    
    # Récupérer le titre
    title_raw = row.get(title_col, '')
    if pd.isna(title_raw):
        title_raw = ''
    title = clean_text(str(title_raw))
    
    # Si pas de titre, retourner None pour ignorer cette vidéo
    if not title or len(title.strip()) == 0:
        return None, None
    
    # Limiter le titre à 100 caractères
    if len(title) > 100:
        title = title[:97] + "..."
    
    # Récupérer la description
    if desc_col:
        desc_raw = row.get(desc_col, '')
        if pd.isna(desc_raw):
            desc_raw = ''
        description = str(desc_raw)
    else:
        description = ''
    
    return title, description

def main():
    """Fonction principale."""
    # Parser les arguments
    parser = argparse.ArgumentParser(description='Upload automatique de vidéos YouTube multilingue')
    parser.add_argument('--langs', '-l', nargs='+', help='Langues à traiter (ex: fr es de)')
    parser.add_argument('--all', '-a', action='store_true', help='Traiter toutes les langues')
    parser.add_argument('--list', action='store_true', help='Lister les langues disponibles')
    parser.add_argument('--save-config', action='store_true', help='Sauvegarder la sélection dans le fichier de config')
    
    args = parser.parse_args()
    
    # Trouver tous les dossiers de langues disponibles
    all_lang_dirs = get_language_dirs()
    if not all_lang_dirs:
        print("❌ Aucun dossier de langue trouvé")
        sys.exit(1)
    
    # Lister les langues disponibles
    if args.list:
        print("🌍 Langues disponibles:")
        for lang_dir in all_lang_dirs:
            print(f"  - {lang_dir.name}")
        return
    
    # Déterminer quelles langues traiter
    selected_languages = None
    if args.langs:
        selected_languages = args.langs
    elif args.all:
        selected_languages = None  # Toutes les langues
    else:
        # Charger depuis le fichier de config
        config_langs = load_config()
        if config_langs:
            selected_languages = config_langs
        else:
            # Par défaut: toutes les langues
            selected_languages = None
    
    # Filtrer les langues
    lang_dirs = filter_language_dirs(all_lang_dirs, selected_languages)
    
    if not lang_dirs:
        print("❌ Aucune langue sélectionnée ou trouvée")
        if selected_languages:
            print(f"   Langues demandées: {', '.join(selected_languages)}")
            print(f"   Langues disponibles: {', '.join([d.name for d in all_lang_dirs])}")
        sys.exit(1)
    
    # Sauvegarder la config si demandé
    if args.save_config and selected_languages:
        save_config(selected_languages)
        print(f"✅ Configuration sauvegardée: {', '.join(selected_languages)}")
    
    print("=" * 70)
    print("🚀 SCRIPT D'UPLOAD YOUTUBE MULTILINGUE")
    print("=" * 70)
    print()
    
    # Charger le tracking
    tracking_data = load_tracking()
    
    # Vérifier le quota du jour
    uploads_today = get_uploads_today(tracking_data)
    
    if DAILY_QUOTA is not None:
        remaining_quota = DAILY_QUOTA - uploads_today
        print(f"📊 Quota du jour: {uploads_today}/{DAILY_QUOTA} vidéos uploadées")
        print(f"   Reste: {remaining_quota} vidéos aujourd'hui")
        print()
        
        if remaining_quota <= 0:
            print("⚠️  Quota quotidien atteint. Le script continuera demain automatiquement.")
            print("   Le script sera relancé automatiquement demain via le scheduler.")
            return
    else:
        print(f"📊 Vidéos uploadées aujourd'hui: {uploads_today}")
        print("   Pas de limite de quota définie")
        print()
    
    print(f"🌍 Langues sélectionnées: {', '.join([d.name for d in lang_dirs])}")
    print()
    
    # Authentifier YouTube
    print("🔐 Authentification YouTube...")
    try:
        youtube = get_authenticated_service()
        print("✅ Authentification réussie")
        print()
    except Exception as e:
        print(f"❌ Erreur lors de l'authentification: {e}")
        sys.exit(1)
    
    # Parcourir chaque langue
    total_uploaded = 0
    total_skipped = 0
    total_errors = 0
    
    for lang_dir in lang_dirs:
        lang_code = get_lang_code_from_dir(lang_dir)
        lang_name = "Principal (EN)" if lang_dir == ROOT_DIR else lang_code.upper()
        print(f"\n{'='*70}")
        print(f"🌍 Langue: {lang_name}")
        print(f"{'='*70}")
        
        # Charger le CSV de cette langue
        df = load_csv_data(lang_dir)
        if df is None:
            print(f"⚠️  Impossible de charger le CSV pour {lang_code}")
            continue
        
        # Vérifier si la colonne youtube_url existe et la convertir en string
        if 'youtube_url' not in df.columns:
            df['youtube_url'] = ''
        else:
            # Convertir en string dès le début pour éviter les problèmes de type
            df['youtube_url'] = df['youtube_url'].fillna('').astype(str)
        
        # Récupérer l'URL du site
        site_url = get_site_url(lang_dir)
        print(f"🌐 URL du site: {site_url}")
        
        # Chercher la colonne ID (peut être 'id' ou 'product_id')
        id_col = 'id' if 'id' in df.columns else 'product_id'
        if id_col not in df.columns:
            print(f"⚠️  Colonne ID non trouvée dans le CSV (cherché 'id' ou 'product_id')")
            continue
        
        # Parcourir les produits
        products_with_videos = []
        for _, row in df.iterrows():
            product_id = str(row.get(id_col, ''))
            if not product_id:
                continue
            
            # Vérifier si déjà uploadé pour cette langue
            if is_already_uploaded(tracking_data, lang_code, product_id):
                continue
            
            # Chercher une vidéo dans le dossier du produit
            product_folder = IMAGES_DIR / product_id
            video_file = find_video_in_folder(product_folder)
            
            if video_file:
                products_with_videos.append((product_id, video_file))
        
        print(f"📹 {len(products_with_videos)} vidéo(s) trouvée(s) pour {lang_code}")
        
        # Uploader les vidéos (dans la limite du quota)
        for product_id, video_file in products_with_videos:
            # Vérifier le quota
            if not can_upload_today(tracking_data):
                if DAILY_QUOTA is not None:
                    print(f"\n⚠️  Quota quotidien atteint ({DAILY_QUOTA} vidéos)")
                    print("   Les vidéos restantes seront uploadées demain automatiquement.")
                break
            
            print(f"\n📹 Produit {product_id}: {video_file.name}")
            
            # Récupérer les métadonnées
            title, description_short = get_product_metadata(df, product_id, lang_code)
            if not title:
                print(f"  ⚠️  Titre non trouvé dans le CSV, vidéo ignorée")
                total_skipped += 1
                continue
            
            # Construire la description
            description = build_description(product_id, description_short, site_url, lang_code)
            
            # Uploader la vidéo
            youtube_url = upload_video(youtube, video_file, title, description, privacy_status='public')
            
            if youtube_url:
                # Enregistrer dans le tracking
                record_upload(tracking_data, lang_code, product_id, youtube_url)
                
                # Mettre à jour le CSV
                id_col = 'id' if 'id' in df.columns else 'product_id'
                # Trouver l'index du produit (convertir les deux en string pour la comparaison)
                product_mask = df[id_col].astype(str) == str(product_id)
                # Mettre à jour l'URL YouTube
                df.loc[product_mask, 'youtube_url'] = youtube_url
                # Sauvegarder immédiatement après chaque upload
                save_csv_data(lang_dir, df)
                
                total_uploaded += 1
                uploads_today = get_uploads_today(tracking_data)
                if DAILY_QUOTA is not None:
                    print(f"  ✅ Upload réussi ({uploads_today}/{DAILY_QUOTA} aujourd'hui)")
                else:
                    print(f"  ✅ Upload réussi ({uploads_today} aujourd'hui)")
            else:
                total_errors += 1
                print(f"  ❌ Échec de l'upload")
        
        # Compter les vidéos ignorées (déjà uploadées)
        skipped = sum(1 for pid, _ in products_with_videos 
                     if is_already_uploaded(tracking_data, lang_code, pid))
        total_skipped += skipped
    
    # Sauvegarder le tracking
    save_tracking(tracking_data)
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print(f"✅ Vidéos uploadées aujourd'hui: {total_uploaded}")
    print(f"⏭️  Vidéos ignorées (déjà uploadées): {total_skipped}")
    print(f"❌ Erreurs: {total_errors}")
    uploads_today = get_uploads_today(tracking_data)
    if DAILY_QUOTA is not None:
        print(f"📊 Quota utilisé: {uploads_today}/{DAILY_QUOTA}")
    else:
        print(f"📊 Vidéos uploadées aujourd'hui: {uploads_today}")
    
    # Vérifier s'il reste des vidéos à uploader
    remaining_videos = check_remaining_videos(tracking_data, lang_dirs)
    if remaining_videos > 0:
        print(f"\n📹 Il reste {remaining_videos} vidéo(s) à uploader")
        print(f"💡 Le script sera relancé automatiquement demain à 9h00")
    else:
        print(f"\n✅ Toutes les vidéos ont été uploadées pour les langues sélectionnées !")
    print("=" * 70)

if __name__ == "__main__":
    main()

