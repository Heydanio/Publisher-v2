import os
import json
import sys

def upload_to_tiktok(config, video_path, video_title):
    # --- CONFIGURATION DES CHEMINS ---
    current_dir = os.getcwd()
    upstream_path = os.path.join(current_dir, "upstream")
    
    if upstream_path not in sys.path:
        sys.path.insert(0, upstream_path)

    try:
        # Import de la fonction d'upload au lieu de la classe
        from tiktok_uploader.uploader import upload_video
        print("✅ Moteur Makiisthenes chargé (Fonction upload_video).")
    except Exception as e:
        print(f"🔥 Erreur d'importation : {e}")
        return False

    # --- PRÉPARATION ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    # Dossier pour les cookies comme attendu par le moteur
    os.makedirs("CookiesDir", exist_ok=True)
    cookie_file = os.path.join("CookiesDir", f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    # Nettoyage du titre pour la description
    clean_title = video_title.replace(".mp4", "")
    tags = config.get("tags", ["#fyp", "#viral"])
    description = f"{clean_title} {' '.join(tags)}"

    # --- EXECUTION ---
    try:
        print(f"🚀 [Makiisthenes] Upload de : {video_path.name}")
        
        # Appel de la fonction officielle du repo
        success = upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file
        )
        
        if success:
            print(f"✅ Vidéo envoyée à TikTok !")
            return True
        else:
            print("❌ Le moteur a retourné un échec.")
            return False

    except Exception as e:
        print(f"❌ Erreur pendant l'exécution : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)