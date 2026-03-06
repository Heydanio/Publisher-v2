import os
import json
import sys
import importlib.util

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. LOCALISATION PRÉCISE DU MOTEUR ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    # Chemin exact basé sur ton log : engine/tiktok_uploader/uploader.py
    uploader_path = os.path.join(engine_dir, "tiktok_uploader", "uploader.py")
            
    if not os.path.exists(uploader_path):
        print(f"❌ Erreur : uploader.py est introuvable au chemin : {uploader_path}")
        # Sécurité : on regarde si par hasard il est ailleurs
        return False

    # --- 2. CHARGEMENT CHIRURGICAL DU MOTEUR ---
    # On ajoute le dossier parent du package pour que les imports relatifs fonctionnent
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)

    try:
        spec = importlib.util.spec_from_file_location("uploader", uploader_path)
        uploader = importlib.util.module_from_spec(spec)
        sys.modules["uploader"] = uploader
        spec.loader.exec_module(uploader)
        print(f"✅ Moteur chargé avec succès depuis {uploader_path}")
    except Exception as e:
        print(f"🔥 Erreur lors du chargement du moteur : {e}")
        return False

    # --- 3. PRÉPARATION DES DONNÉES ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp', '#viral']))}"

    # --- 4. LANCEMENT DE L'UPLOAD ---
    try:
        print(f"🚀 [Makiisthenes] Upload en cours : {video_path.name}")
        
        # On utilise la fonction du repo
        success = uploader.upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file
        )
        
        return success

    except Exception as e:
        print(f"❌ Erreur exécution moteur : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)