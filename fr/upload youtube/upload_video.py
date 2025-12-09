#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour uploader des vidéos sur YouTube
Utilise l'API YouTube Data API v3
"""

import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import json

# Scopes nécessaires pour uploader des vidéos
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Nom du fichier client secrets (à adapter selon votre fichier)
CLIENT_SECRETS_FILE = 'client_secret_938787798816-u7frdh82p7pckpj8hodtr3i1ss3fcjfu.apps.googleusercontent.com.json'

# Fichier pour sauvegarder les credentials (token)
CREDENTIALS_FILE = 'credentials.json'

def get_authenticated_service():
    """Authentifie l'utilisateur et retourne le service YouTube."""
    credentials = None
    
    # Vérifier si on a déjà des credentials sauvegardés
    if os.path.exists(CREDENTIALS_FILE):
        try:
            credentials = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
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
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"❌ Fichier client secrets non trouvé: {CLIENT_SECRETS_FILE}")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Sauvegarder les credentials pour la prochaine fois
        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(credentials.to_json())
    
    return build('youtube', 'v3', credentials=credentials)

def upload_video(youtube, video_file, title, description='', tags=None, category_id='22', privacy_status='private'):
    """
    Upload une vidéo sur YouTube.
    
    Args:
        youtube: Service YouTube authentifié
        video_file: Chemin vers le fichier vidéo
        title: Titre de la vidéo
        description: Description de la vidéo
        tags: Liste de tags (optionnel)
        category_id: ID de la catégorie (22 = People & Blogs par défaut)
        privacy_status: 'private', 'public', ou 'unlisted'
    
    Returns:
        L'ID de la vidéo uploadée ou None en cas d'erreur
    """
    if not os.path.exists(video_file):
        print(f"❌ Fichier vidéo non trouvé: {video_file}")
        return None
    
    # Préparer les métadonnées de la vidéo
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }
    
    # Créer l'objet MediaFileUpload
    media = MediaFileUpload(
        video_file,
        chunksize=-1,
        resumable=True,
        mimetype='video/*'
    )
    
    try:
        print(f"📤 Upload de la vidéo: {video_file}")
        print(f"📝 Titre: {title}")
        print(f"🔒 Statut: {privacy_status}")
        print("⏳ Upload en cours...")
        
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
                        print(f"✅ Vidéo uploadée avec succès!")
                        print(f"🔗 ID de la vidéo: {video_id}")
                        print(f"🌐 URL: https://www.youtube.com/watch?v={video_id}")
                        return video_id
                    else:
                        print(f"❌ Erreur lors de l'upload: {response}")
                        return None
                else:
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"\r📊 Progression: {progress}%", end='', flush=True)
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"Erreur {e.resp.status}: {e.content}"
                    retry += 1
                    if retry < 5:
                        print(f"\n⚠️  Erreur temporaire, nouvelle tentative ({retry}/5)...")
                        continue
                    else:
                        print(f"\n❌ Erreur après {retry} tentatives: {error}")
                        return None
                else:
                    print(f"\n❌ Erreur HTTP: {e}")
                    return None
        
        return None
        
    except HttpError as e:
        print(f"❌ Erreur HTTP lors de l'upload: {e}")
        if e.resp.status == 403:
            print("💡 Vérifiez que l'API YouTube Data API v3 est activée dans Google Cloud Console")
        return None
    except Exception as e:
        print(f"❌ Erreur lors de l'upload: {e}")
        return None

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🚀 SCRIPT D'UPLOAD YOUTUBE")
    print("=" * 70)
    print()
    
    # Vérifier les arguments
    if len(sys.argv) < 3:
        print("Usage: python3 upload_video.py <fichier_video> <titre> [description] [tags] [privacy]")
        print()
        print("Exemples:")
        print("  python3 upload_video.py video.mp4 'Mon titre'")
        print("  python3 upload_video.py video.mp4 'Mon titre' 'Ma description'")
        print("  python3 upload_video.py video.mp4 'Mon titre' 'Ma description' 'tag1,tag2' 'public'")
        print()
        print("Privacy: 'private' (défaut), 'public', ou 'unlisted'")
        sys.exit(1)
    
    video_file = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ''
    tags_str = sys.argv[4] if len(sys.argv) > 4 else ''
    privacy_status = sys.argv[5] if len(sys.argv) > 5 else 'private'
    
    # Parser les tags
    tags = [tag.strip() for tag in tags_str.split(',')] if tags_str else []
    
    # Authentifier et obtenir le service YouTube
    try:
        youtube = get_authenticated_service()
        print("✅ Authentification réussie")
        print()
    except Exception as e:
        print(f"❌ Erreur lors de l'authentification: {e}")
        sys.exit(1)
    
    # Uploader la vidéo
    video_id = upload_video(
        youtube,
        video_file,
        title,
        description,
        tags,
        privacy_status=privacy_status
    )
    
    if video_id:
        print()
        print("=" * 70)
        print("✅ UPLOAD TERMINÉ AVEC SUCCÈS!")
        print("=" * 70)
    else:
        print()
        print("=" * 70)
        print("❌ ÉCHEC DE L'UPLOAD")
        print("=" * 70)
        sys.exit(1)

if __name__ == '__main__':
    main()

