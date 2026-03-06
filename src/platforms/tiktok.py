import os
import json
import sys
import shutil

# On ajoute le dossier "engine" au chemin Python pour pouvoir l'utiliser
sys.path.append(os.path.join(os.getcwd(), "engine"))
from engine.tiktok_uploader.uploader import upload_video

def upload_to_tiktok(config, video_path, video_title):
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    # Le repo Makiisthenes a besoin d'un FICHIER de cookies, pas d'un texte
    cookie_file = f"cookies_{account_id}.json"
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    print(f"🚀 [Makiisthenes-Engine] Lancement de l'upload direct...")
    
    tags = config.get("tags", ["#fyp"])
    description = f"{video_title.replace('.mp4', '')} {' '.join(tags)}"

    try:
        # On appelle directement la fonction officielle du repo
        # Elle va automatiquement appeler Node.js pour la signature
        success = upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file,
            session_id=None # On utilise les cookies à la place
        )
        
        if success:
            print(f"✅ TikTok : Publication réussie avec signatures Node.js !")
            return True
        else:
            print(f"❌ L'upload a échoué (vérifie les cookies ou le fichier Node)")
            return False
            
    except Exception as e:
        print(f"🔥 Erreur moteur : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)