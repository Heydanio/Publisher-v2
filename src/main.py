import os
import sys
import json
import tempfile
import random
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Correctif pour les émojis sur le terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Import de nos modules ---
from core.state import mark_video_published
from core.drive import get_unpublished_video, download_video
from platforms.youtube import upload_to_youtube
from platforms.tiktok import upload_to_tiktok
from core.alert import send_discord_notification

# On travaille toujours en heure de Paris
PARIS_TZ = ZoneInfo("Europe/Paris")

def load_config(account_name: str) -> dict:
    config_path = Path(f"config/{account_name}.json")
    if not config_path.exists():
        print(f"❌ Erreur : Config introuvable ({config_path})")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    account_name = os.environ.get("ACCOUNT_NAME", "youtube_compte1")
    print(f"\n🚀 Démarrage de l'Auto-Publisher V2 : {account_name}")
    
    config = load_config(account_name)
    platform = config.get("platform", "youtube")
    account_id = config.get("account_id")
    
    # --- GESTION DE L'ID DRIVE (CORRIGÉE) ---
    # On initialise folder_ids à vide
    folder_ids = []
    
    # 1. On regarde si une liste existe dans le JSON
    json_folder_ids = config.get("drive_folder_ids", [])
    # 2. On regarde si un ID unique existe dans le JSON (sans 's')
    json_single_id = config.get("drive_folder_id")
    
    if json_folder_ids:
        folder_ids = json_folder_ids
    elif json_single_id:
        folder_ids = [json_single_id]

    # 3. Si on trouve le mot-clé SECRET, on va chercher dans les secrets GitHub
    if folder_ids and (folder_ids[0] == "SECRET_DRIVE_FOLDER_ID" or folder_ids[0] == ""):
        secret_id = os.environ.get("DRIVE_FOLDER_ID")
        if secret_id:
            folder_ids = [secret_id]
            print(f"🔑 ID Drive récupéré depuis GitHub : {secret_id[:5]}...")
        else:
            print("⚠️ Attention : SECRET_DRIVE_FOLDER_ID attendu mais la variable d'env DRIVE_FOLDER_ID est vide.")
            folder_ids = []

    # --- VÉRIFICATION DE L'HEURE ---
    now_paris = datetime.now(PARIS_TZ)
    current_hour = now_paris.hour
    current_min = now_paris.minute
    
    force_post = os.environ.get("FORCE_POST") == "1"
    scheduled_hours = config.get("schedule", {}).get("slots_hours", [])
    
    is_time_to_post = current_hour in scheduled_hours
    is_within_margin = current_min < 55 

    print(f"📅 Heure actuelle (Paris) : {current_hour}h{current_min:02d}")

    if not force_post:
        if not is_time_to_post:
            print(f"⏳ Pas de publication prévue à {current_hour}h.")
            return
        
        if not is_within_margin:
            send_discord_notification(f"⏰ **{account_id}** : Créneau de {current_hour}h raté (trop de retard GitHub).")
            print(f"⏳ Créneau de {current_hour}h presque fini.")
            return

        # --- SIMULATION HUMAINE (Délai aléatoire) ---
        wait_min = random.randint(1, 10)
        send_discord_notification(f"🎲 **{account_id}** : Créneau {current_hour}h détecté ! Attente de `{wait_min} min` avant postage...")
        print(f"🎲 Jitter : Attente de {wait_min} minutes...")
        time.sleep(wait_min * 60)
        
        # Recalcul de l'heure après attente
        now_paris = datetime.now(PARIS_TZ)
        current_hour = now_paris.hour
        current_min = now_paris.minute

    print(f"✅ Mode publication activé pour {account_id} ({platform}) !")

    # --- RECHERCHE DE VIDÉO ---
    if not folder_ids:
        print("❌ ERREUR : Aucun ID de dossier Drive n'a pu être trouvé.")
        return

    video = get_unpublished_video(account_name, folder_ids, platform=platform)
    
    if not video:
        print("🛑 Aucune vidéo inédite trouvée.")
        return

    # --- TÉLÉCHARGEMENT ---
    tmpdir = Path(tempfile.mkdtemp())
    # Nettoyage sommaire du nom de fichier pour éviter les erreurs locales
    safe_name = "".join([c for c in video["name"] if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
    local_video_path = tmpdir / safe_name
    
    download_video(video["id"], local_video_path)

    # --- UPLOAD ---
    success = False
    try:
        if platform == "youtube":
            success = upload_to_youtube(config, local_video_path, video["name"])
        elif platform == "tiktok":
            success = upload_to_tiktok(config, local_video_path, video["name"])
    except Exception as e:
        print(f"❌ Erreur pendant l'upload : {e}")
        success = False

    # --- FINALISATION ---
    if success:
        try:
            mark_video_published(account_name, video["id"], platform=platform)
            print("✅ Statut mis à jour dans Supabase.")
        except Exception as e:
            print(f"⚠️ Alerte : Impossible de mettre à jour Supabase ({e}), mais la vidéo est publiée !")
        send_discord_notification(
            f"✅ **PUBLICATION RÉUSSIE ({platform.upper()})**\n"
            f"👤 **Compte :** {account_id}\n"
            f"🎬 **Vidéo :** `{video['name']}`\n"
            f"⏰ **Heure :** {current_hour}h{current_min:02d}"
        )
    else:
        send_discord_notification(f"❌ **ERREUR** : L'upload {platform} a échoué pour **{account_id}**.")

    # --- NETTOYAGE ---
    if local_video_path.exists():
        os.remove(local_video_path)
        print("🧹 Fichier temporaire supprimé.")

if __name__ == "__main__":
    main()