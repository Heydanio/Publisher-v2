import os
import json
import sys
import importlib.util

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. LOCALISATION DU MOTEUR ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    # On cherche uploader.py là où il peut se cacher
    possible_paths = [
        os.path.join(engine_dir, "tiktok_uploader", "uploader.py"),
        os.path.join(engine_dir, "uploader.py")
    ]
    
    uploader_path = None
    for p in possible_paths:
        if os.path.exists(p):
            uploader_path = p
            break
            
    if not uploader_path:
        print(f"❌ Erreur : Impossible de trouver uploader.py dans {engine_dir}")
        if os.path.exists(engine_dir):
            print(f"📁 Contenu trouvé dans engine : {os.listdir(engine_dir)}")
        return False

    # --- 2. CHARGEMENT CHIRURGICAL DU MOTEUR ---
    # On ajoute les dossiers au path pour que les imports internes du moteur fonctionnent
    sys.path.insert(0, engine_dir)
    sys.path.insert(0, os.path.join(engine_dir, "tiktok_uploader"))

    try:
        spec = importlib.util.spec_from_file_location("uploader", uploader_path)
        uploader = importlib.util.module_from_spec(spec)
        sys.modules["uploader"] = uploader
        spec.loader.exec_module(uploader)
        print(f"✅ Moteur chargé depuis : {uploader_path}")
    except Exception as e:
        print(f"🔥 Erreur lors du chargement du moteur : {e}")
        return False

    # --- 3. PRÉPARATION DES DONNÉES ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    # Le moteur nécessite un fichier JSON physique pour les cookies
    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    # Nettoyage du titre et ajout des tags
    clean_title = video_title.replace(".mp4", "")
    tags = config.get("tags", ["#fyp", "#viral"])
    description = f"{clean_title} {' '.join(tags)}"

    # --- 4. LANCEMENT DE L'UPLOAD ---
    try:
        print(f"🚀 [Makiisthenes-Engine] Tentative d'upload : {video_path.name}")
        
        # Appel de la fonction de base du repo
        # Note: uploader.upload_video va appeler le script Node.js pour la signature X-Bogus
        success = uploader.upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file
        )
        
        if success:
            print(f"✅ TikTok : Publication réussie pour {video_title} !")
            return True
        else:
            print("❌ Le moteur a retourné un échec (vérifie les cookies ou la signature Node).")
            return False

    except Exception as e:
        print(f"❌ Erreur critique pendant l'upload : {e}")
        return False
    finally:
        # Nettoyage du fichier cookie temporaire
        if os.path.exists(cookie_file):
            os.remove(cookie_file)