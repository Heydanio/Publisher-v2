import os
import io
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import base64
import json
from core.state import is_video_published

def get_drive_service():
    """Initialise le service Google Drive avec nettoyage automatique des données."""
    encoded_json = os.environ.get("GDRIVE_SA_JSON_B64")
    if not encoded_json:
        raise ValueError("❌ Erreur : GDRIVE_SA_JSON_B64 manquant dans les secrets GitHub.")
    
    try:
        # 1. Nettoyage des espaces/sauts de ligne dans la chaîne base64
        encoded_json = encoded_json.strip()
        
        # 2. Décodage
        decoded_json = base64.b64decode(encoded_json).decode('utf-8').strip()
        
        # 3. Correction des caractères parasites (Extra data / BOM)
        # On cherche la première accolade pour ignorer tout ce qui est avant
        start_index = decoded_json.find('{')
        if start_index != -1:
            decoded_json = decoded_json[start_index:]
        
        # 4. Chargement JSON
        service_account_info = json.loads(decoded_json)
        
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Erreur critique lors du chargement de la clé Google Drive : {str(e)}")
        raise

def get_unpublished_video(account_name, folder_ids, platform="youtube"):
    """Cherche une vidéo inédite sur CETTE plateforme."""
    service = get_drive_service()
    
    for folder_id in folder_ids:
        print(f"📁 Recherche dans le dossier Drive : {folder_id}...")
        query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        for item in items:
            video_id = item['id']
            video_name = item['name']
            
            # Vérification par compte ET par plateforme
            if not is_video_published(account_name, video_id, platform=platform):
                print(f"✨ Nouvelle vidéo trouvée : {video_name} (ID: {video_id})")
                return item
            else:
                print(f"⏩ Vidéo déjà publiée sur {platform} : {video_name}")
                
    return None

def download_video(file_id, local_path):
    """Télécharge la vidéo vers le serveur temporaire de GitHub."""
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    print(f"📥 Téléchargement en cours...")
    while done is False:
        status, done = downloader.next_chunk()
    print(f"✅ Téléchargement terminé : {local_path}")