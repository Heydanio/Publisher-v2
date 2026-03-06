import os
import json
import sys
import importlib.util

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. SCAN TOTAL POUR TROUVER UPLOADER.PY ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    uploader_path = None
    print(f"🔍 Scan de survie dans {engine_dir}...")
    
    for root, dirs, files in os.walk(engine_dir):
        if "uploader.py" in files:
            uploader_path = os.path.join(root, "uploader.py")
            break
            
    if not uploader_path:
        print(f"❌ MORT : uploader.py est introuvable dans tout le dossier engine.")
        # Liste récursive pour comprendre ce qui se passe
        for root, dirs, files in os.walk(engine_dir):
            print(f"📁 {root}: {files}")
        return False

    print(f"🎯 TROUVÉ : {uploader_path}")

    # --- 2. CHARGEMENT CHIRURGICAL ---
    # On ajoute le dossier parent du fichier trouvé au path
    parent_dir = os.path.dirname(uploader_path)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)

    try:
        spec = importlib.util.spec_from_file_location("uploader", uploader_path)
        uploader = importlib.util.module_from_spec(spec)
        sys.modules["uploader"] = uploader
        spec.loader.exec_module(uploader)
        print("✅ Moteur chargé.")
    except Exception as e:
        print(f"🔥 Erreur chargement : {e}")
        return False

    # --- 3. PRÉPARATION ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")
    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp']))}"

    # --- 4. UPLOAD ---
    try:
        print(f"🚀 [Makiisthenes] Upload de {video_path.name}")
        # On appelle la fonction telle qu'elle est définie dans le repo
        success = uploader.upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file
        )
        return success
    except Exception as e:
        print(f"❌ Erreur exécution : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)