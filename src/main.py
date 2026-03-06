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
    platform = config.get("platform")
    account_id = config.get("account_id")
    
    # --- GESTION DE L'ID DRIVE CACHÉ ---
    folder_ids = config.get("drive_folder_ids", [])
    if folder_ids and folder_ids[0] == "SECRET_DRIVE_FOLDER_ID":
        secret_id = os.environ.get("DRIVE_FOLDER_ID")
        if secret_id:
            folder_ids = [secret_id]
            print("🔑 ID Drive récupéré depuis les secrets sécurisés.")

    # --- VÉRIFICATION DE L'HEURE ---
    now_paris = datetime.now(PARIS_TZ)
    current_hour = now_paris.hour
    current_min = now_paris.minute
    
    force_post = os.environ.get("FORCE_POST") == "1"
    scheduled_hours = config.get("schedule", {}).get("slots_hours", [])
    
    is_time_to_post = current_hour in scheduled_hours
    is_within_margin = current_min < 55 # Marge large pour le délai aléatoire

    print(f"📅 Heure actuelle (Paris) : {current_hour}h{current_min:02d}")

    if not force_post:
        if not is_time_to_post:
            print(f"⏳ Pas de publication prévue à {current_hour}h.")
            return
        if not is_within_margin:
            print(f"⏳ Créneau de {current_hour}h presque fini.")
            return

        # --- SIMULATION HUMAINE (Délai aléatoire) ---
        wait_min = random.randint(1, 20)
        print(f"🎲 Jitter : Attente de {wait_min} minutes pour varier l'heure de post...")
        time.sleep(wait_min * 60)
        
        # Recalcul de l'heure après attente
        now_paris = datetime.now(PARIS_TZ)
        current_hour = now_paris.hour
        current_min = now_paris.minute

    print(f"✅ Mode publication activé pour {account_id} !")

    video = get_unpublished_video(account_name, folder_ids)
    if not video:
        print("🛑 Aucune vidéo inédite trouvée.")
        return

    tmpdir = Path(tempfile.mkdtemp())
    local_video_path = tmpdir / video["name"]
    download_video(video["id"], local_video_path)

    if platform == "youtube":
        success = upload_to_youtube(config, local_video_path, video["name"])
        if success:
            mark_video_published(account_name, video["id"])
            send_discord_notification(
                f"✅ **PUBLICATION RÉUSSIE**\n📺 **Chaîne :** {account_id}\n🎬 **Vidéo :** `{video['name']}`\n⏰ **Heure :** {current_hour}h{current_min:02d}"
            )
        else:
            send_discord_notification(f"⚠️ **ÉCHEC PUBLICATION** sur {account_id}")

    if local_video_path.exists():
        os.remove(local_video_path)

if __name__ == "__main__":
    main()