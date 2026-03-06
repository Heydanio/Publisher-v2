import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Correctif pour les émojis sur le terminal Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Import de nos modules ---
from core.state import mark_video_published
from core.drive import get_unpublished_video, download_video
from platforms.youtube import upload_to_youtube

PARIS_TZ = ZoneInfo("Europe/Paris")

def load_config(account_name: str) -> dict:
    """Charge le fichier JSON de configuration du compte."""
    config_path = Path(f"config/{account_name}.json")
    if not config_path.exists():
        print(f"❌ Erreur : Config introuvable ({config_path})")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # 1. Quel compte on utilise ?
    account_name = os.environ.get("ACCOUNT_NAME", "youtube_compte1")
    print(f"\n🚀 Démarrage de l'Auto-Publisher V2 pour : {account_name}")
    
    config = load_config(account_name)
    platform = config.get("platform")
    account_id = config.get("account_id")
    
    print(f"📋 Plateforme cible : {platform.upper()} (ID Compte: {account_id})")

    # Mode test : On s'assure qu'on veut forcer la publication pour tester
    if os.environ.get("FORCE_POST") != "1":
        print(f"⏳ {datetime.now(PARIS_TZ).strftime('%H:%M')} - Pas l'heure de publier. Ajoute $env:FORCE_POST='1' pour tester.")
        return

    print("\n✅ Mode FORCE_POST activé. Recherche d'une vidéo...")

    # 2. Chercher une vidéo inédite sur Drive (qui n'est pas dans Supabase)
    folder_ids = config.get("drive_folder_ids", [])
    video = get_unpublished_video(account_name, folder_ids)
    
    if not video:
        print("🛑 Aucune vidéo inédite trouvée. Fin du script.")
        return

    # 3. Télécharger la vidéo temporairement sur le PC
    tmpdir = Path(tempfile.mkdtemp())
    local_video_path = tmpdir / video["name"]
    download_video(video["id"], local_video_path)

    # 4. Aiguillage et Upload
    if platform == "youtube":
        print("\n▶️ Lancement du module YOUTUBE...")
        success = upload_to_youtube(config, local_video_path, video["name"])
        
        if success:
            # 5. Si YouTube dit OK, on sauvegarde définitivement dans la base de données !
            mark_video_published(account_name, video["id"])
            print("🎉 BINGO ! Publication terminée et historique mis à jour !")
        else:
            print("❌ La publication a échoué. L'historique n'est pas mis à jour pour pouvoir réessayer plus tard.")
            
    elif platform == "tiktok":
        print("\n🎵 Module TIKTOK en attente d'intégration...")
        # On fera ça juste après !
        
    else:
        print(f"❌ Plateforme inconnue : {platform}")

    # 6. Nettoyage : On supprime la vidéo du PC pour ne pas saturer le disque dur
    try:
        os.remove(local_video_path)
        print("🧹 Fichier vidéo temporaire supprimé du PC.")
    except Exception:
        pass

if __name__ == "__main__":
    main()