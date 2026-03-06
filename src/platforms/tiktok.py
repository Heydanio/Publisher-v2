import os
import json
import sys

def upload_to_tiktok(config, video_path, video_title):
    # --- CONFIGURATION DU PYTHONPATH ---
    current_dir = os.getcwd()
    upstream_dir = os.path.join(current_dir, "upstream")
    
    if upstream_dir not in sys.path:
        sys.path.insert(0, upstream_dir)

    try:
        # Importation via le package tiktok_uploader situé dans upstream
        from tiktok_uploader.uploader import upload_video
        print("✅ Moteur Makiisthenes chargé avec succès.")
    except ImportError as e:
        print(f"🔥 Erreur d'importation : {e}")
        # Debug : Lister les dossiers pour voir où on est
        if os.path.exists(upstream_dir):
            print(f"Contenu de upstream : {os.listdir(upstream_dir)}")
        return False

    # --- PRÉPARATION DES FICHIERS ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    os.makedirs("CookiesDir", exist_ok=True)
    cookie_file = os.path.join("CookiesDir", f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp']))}"

    # --- EXECUTION ---
    try:
        print(f"🚀 [Makiisthenes] Upload : {video_path.name}")
        
        # Appel de la fonction uploader.py
        success = upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file
        )
        
        return success

    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)