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
    """Version de secours ultime contre l'erreur Extra Data."""
    import re # Ajoute cet import en haut du fichier si besoin
    
    encoded_json = os.environ.get("GDRIVE_SA_JSON_B64", "").strip()
    if not encoded_json:
        raise ValueError("❌ Secret GDRIVE_SA_JSON_B64 vide.")
    
    try:
        # 1. Décodage et nettoyage des espaces
        decoded_json = base64.b64decode(encoded_json).decode('utf-8').strip()
        
        # 2. On utilise une Regex pour ne garder QUE ce qui est entre les premières {}
        # Cela élimine tout caractère "Extra data" invisible à la fin
        match = re.search(r'(\{.*\})', decoded_json, re.DOTALL)
        if match:
            clean_json = match.group(1)
        else:
            clean_json = decoded_json

        # 3. Chargement
        service_account_info = json.loads(clean_json)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        return build('drive', 'v3', credentials=creds)
        
    except Exception as e:
        print(f"❌ Erreur finale : {e}")
        # On affiche la longueur pour comprendre s'il y a un doublon
        if 'decoded_json' in locals():
            print(f"DEBUG: Taille reçue {len(decoded_json)} | Début: {decoded_json[:15]}")
        raise

def get_unpublished_video(account_name, folder_ids, platform="youtube"):
    """Cherche une vidéo avec un maximum de logs pour comprendre le blocage."""
    service = get_drive_service()
    
    if not folder_ids:
        print("❌ ERREUR : Aucun ID de dossier reçu !")
        return None

    for folder_id in folder_ids:
        print(f"📁 Tentative de scan du dossier ID : {folder_id}")
        
        try:
            # On demande d'abord les infos du dossier pour voir si on y a accès
            folder_info = service.files().get(fileId=folder_id, fields="name").execute()
            print(f"✅ Dossier trouvé sur Drive : {folder_info.get('name')}")
            
            query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])

            print(f"📊 Nombre de vidéos trouvées dans ce dossier : {len(items)}")

            for item in items:
                v_id = item['id']
                v_name = item['name']
                
                # On vérifie si Supabase bloque
                is_pub = is_video_published(account_name, v_id, platform=platform)
                if not is_pub:
                    print(f"✨ MATCH : '{v_name}' est prête !")
                    return item
                else:
                    print(f"⏩ Déjà publiée : '{v_name}'")
                    
        except Exception as e:
            print(f"❌ Erreur lors du scan du dossier {folder_id} : {e}")
                
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