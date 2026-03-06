import os
import io
import json
import base64
import random
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# On importe notre fonction Supabase qu'on vient de créer !
from .state import is_video_published

def get_drive_service():
    """Initialise la connexion à l'API Google Drive."""
    sa_b64 = os.environ.get("GDRIVE_SA_JSON_B64")
    if not sa_b64:
        raise ValueError("❌ Erreur : La variable GDRIVE_SA_JSON_B64 est introuvable.")
        
    sa_json = json.loads(base64.b64decode(sa_b64).decode("utf-8"))
    creds = Credentials.from_service_account_info(
        sa_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def list_videos(svc, folder_ids: list) -> list:
    """Liste toutes les vidéos présentes dans les dossiers donnés."""
    all_videos = []
    for fid in folder_ids:
        q = f"'{fid}' in parents and trashed=false"
        fields = "files(id,name,mimeType,size,modifiedTime),nextPageToken"
        page_token = None
        
        while True:
            resp = svc.files().list(
                q=q, spaces="drive", fields=f"nextPageToken,{fields}", pageToken=page_token
            ).execute()
            all_videos.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
                
    # Ne garder que les fichiers vidéos
    return [f for f in all_videos if f["name"].lower().endswith((".mp4", ".mov", ".m4v", ".webm"))]

def get_unpublished_video(account_name: str, folder_ids: list):
    """Trouve une vidéo au hasard qui n'a pas encore été publiée sur ce compte."""
    print("🔍 Recherche de vidéos dans Google Drive...")
    svc = get_drive_service()
    videos = list_videos(svc, folder_ids)
    
    if not videos:
        print("⚠️ Aucune vidéo trouvée dans le(s) dossier(s) Drive.")
        return None
        
    print(f"📂 {len(videos)} vidéos trouvées au total sur le Drive.")
    
    # On mélange pour avoir de l'aléatoire
    random.shuffle(videos)
    
    for vid in videos:
        # C'est ici que la magie de la Phase 2 opère !
        if not is_video_published(account_name, vid["id"]):
            print(f"🎯 Vidéo inédite trouvée : {vid['name']}")
            return vid
            
    print(f"⚠️ Toutes les vidéos de ce dossier ont déjà été publiées sur le compte {account_name} !")
    return None

def download_video(file_id: str, dest_path: Path):
    """Télécharge la vidéo depuis Drive vers le disque dur local."""
    svc = get_drive_service()
    req = svc.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, req)
    
    done = False
    print("⬇️ Début du téléchargement...")
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"⏳ Téléchargement : {int(status.progress() * 100)}%")
    print("✅ Téléchargement terminé !")