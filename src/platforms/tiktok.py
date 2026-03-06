import os
import json
import sys

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. CONFIGURATION DES CHEMINS ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    # On ajoute engine au path pour que les imports internes fonctionnent
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)

    try:
        # Import de la nouvelle classe Tiktok (depuis engine/tiktok_uploader/tiktok.py)
        from tiktok_uploader.tiktok import Tiktok
        print("✅ Moteur Tiktok (v2.0 Class) chargé.")
    except Exception as e:
        print(f"🔥 Erreur lors du chargement de la classe Tiktok : {e}")
        return False

    # --- 2. PRÉPARATION ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    # Le moteur attend un fichier JSON
    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp']))}"

    # --- 3. EXECUTION ---
    try:
        print(f"🚀 [Makiisthenes-V2] Upload de : {video_path.name}")
        
        # Initialisation de la classe avec tes cookies
        bot = Tiktok(cookies=cookie_file)
        
        # Appel de la méthode d'upload
        # filename, description, et d'autres params si besoin
        bot.upload_video(
            filename=str(video_path),
            description=description
        )
        
        print("✅ Publication terminée (via Tiktok Class).")
        return True

    except Exception as e:
        print(f"❌ Erreur pendant l'upload : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)