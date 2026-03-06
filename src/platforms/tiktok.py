import os
import json
import sys
import subprocess

def upload_to_tiktok(config, video_path, video_title):
    # --- CONFIGURATION DES CHEMINS ---
    current_dir = os.getcwd()
    # Le workflow a créé un lien symbolique 'tiktok_uploader' vers 'upstream/tiktok_uploader'
    
    try:
        # Import direct grâce au lien symbolique
        from tiktok_uploader.tiktok import Tiktok
        print("✅ Moteur Tiktok V2 (Upstream) chargé via lien symbolique.")
    except Exception as e:
        print(f"🔥 Erreur d'importation : {e}")
        # Tentative de secours via le dossier upstream direct
        sys.path.append(os.path.join(current_dir, "upstream"))
        from tiktok_uploader.tiktok import Tiktok

    # --- PRÉPARATION ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    # Le moteur cherche les cookies dans CookiesDir par défaut
    os.makedirs("CookiesDir", exist_ok=True)
    cookie_file = os.path.join("CookiesDir", f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp']))}"

    # --- EXECUTION ---
    try:
        print(f"🚀 [Makiisthenes] Upload en cours : {video_path.name}")
        
        # On initialise comme dans ton ancien runner
        bot = Tiktok(cookies=cookie_file)
        
        # Lancement de l'upload
        bot.upload_video(
            filename=str(video_path),
            description=description
        )
        
        print(f"✅ Vidéo envoyée à TikTok !")
        return True

    except Exception as e:
        print(f"❌ Erreur pendant l'exécution : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)