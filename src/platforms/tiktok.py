import os
import json
import sys
import importlib.util

def upload_to_tiktok(config, video_path, video_title):
    # --- CONFIGURATION DU MOTEUR ---
    engine_dir = os.path.join(os.getcwd(), "engine")
    uploader_path = os.path.join(engine_dir, "tiktok_uploader", "uploader.py")
    
    # Ajout au path pour que uploader.py trouve ses voisins
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)
    
    # Import dynamique du fichier uploader.py uniquement
    spec = importlib.util.spec_from_file_location("uploader", uploader_path)
    uploader = importlib.util.module_from_spec(spec)
    
    # Hack pour éviter que uploader.py ne fasse planter l'import de ses propres dépendances
    sys.modules["uploader"] = uploader
    
    try:
        spec.loader.exec_module(uploader)
        print("✅ Moteur d'upload (Uploader.py) chargé.")
    except Exception as e:
        print(f"🔥 Erreur lors du chargement chirurgical du moteur : {e}")
        return False

    # --- PREPARATION DE L'UPLOAD ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    cookie_file = f"cookies_{account_id}.json"
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp']))}"

    try:
        print(f"🚀 Lancement de l'upload via Makiisthenes Engine...")
        # On appelle la fonction du module chargé dynamiquement
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