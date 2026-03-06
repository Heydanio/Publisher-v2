import os
import json
import sys

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. CONFIGURATION DU MOTEUR ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    # Ajout des chemins pour le moteur Makiisthenes
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)
        sys.path.insert(0, os.path.join(engine_dir, "tiktok_uploader"))

    try:
        from tiktok_uploader.tiktok import Tiktok
        print("✅ Moteur Tiktok V2.0 chargé.")
    except Exception as e:
        print(f"🔥 Erreur d'importation : {e}")
        return False

    # --- 2. PRÉPARATION ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")
    
    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp']))}"

    # --- 3. EXÉCUTION ---
    try:
        print(f"🚀 [Makiisthenes-V2] Upload : {video_path.name}")
        bot = Tiktok(cookies=cookie_file)
        
        # Lancement de l'upload
        bot.upload_video(
            filename=str(video_path),
            description=description
        )
        
        print(f"✅ Vidéo transmise avec succès !")
        return True

    except Exception as e:
        print(f"❌ Erreur exécution : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)