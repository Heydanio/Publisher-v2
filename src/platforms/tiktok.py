import os
import json
import sys

# 1. On prépare le terrain pour les imports
current_dir = os.getcwd()
engine_path = os.path.join(current_dir, "engine")

# On ajoute le dossier actuel (où on a créé le faux undetected_chromedriver) 
# et le dossier engine au chemin système
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if engine_path not in sys.path:
    sys.path.insert(1, engine_path)

# 2. Import du moteur
try:
    from tiktok_uploader.uploader import upload_video
    print("✅ Moteur chargé avec succès.")
except Exception as e:
    print(f"⚠️ Note : Import direct échoué, tentative via engine... ({e})")
    from engine.tiktok_uploader.uploader import upload_video

def upload_to_tiktok(config, video_path, video_title):
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    cookie_file = f"cookies_{account_id}.json"
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    print(f"🚀 [Makiisthenes-Engine] Lancement de l'upload réel...")
    
    # Préparation de la légende
    tags = config.get("tags", ["#fyp"])
    description = f"{video_title.replace('.mp4', '')} {' '.join(tags)}"

    try:
        # On appelle le moteur. Le uploader.py de makiisthenes 
        # utilise les signatures Node.js en arrière-plan.
        success = upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file
        )
        
        return success
            
    except Exception as e:
        print(f"🔥 Erreur pendant l'exécution du moteur : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)