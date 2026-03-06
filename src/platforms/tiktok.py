import os
import json
import sys
from unittest.mock import MagicMock

# --- HACK ANTI-DÉPENDANCE : Injection de faux modules ---
# On neutralise moviepy, pytube et les autres avant même que le moteur n'essaie de les charger
for module_name in ["moviepy", "moviepy.editor", "undetected_chromedriver", "pytube"]:
    mock = MagicMock()
    sys.modules[module_name] = mock
    # On mock aussi les sous-propriétés pour éviter les AttributeError
    sys.modules[f"{module_name}.editor"] = mock

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. CONFIGURATION DU MOTEUR ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    # On force l'accès aux dossiers du moteur
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)
        sys.path.insert(0, os.path.join(engine_dir, "tiktok_uploader"))

    try:
        # Import de la classe Tiktok officielle (V2.0)
        from tiktok_uploader.tiktok import Tiktok
        print("✅ Moteur Tiktok V2.0 (Class) chargé (Mode Mock actif).")
    except Exception as e:
        print(f"🔥 Erreur d'importation fatale : {e}")
        return False

    # --- 2. PRÉPARATION DES DONNÉES ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    # Création du fichier de cookies physique requis par le moteur
    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    # Nettoyage du titre et préparation de la légende
    clean_title = video_title.replace(".mp4", "")
    tags = config.get("tags", ["#fyp", "#viral"])
    description = f"{clean_title} {' '.join(tags)}"

    # --- 3. EXÉCUTION DE L'UPLOAD ---
    try:
        print(f"🚀 [Makiisthenes-V2] Tentative d'envoi : {video_path.name}")
        
        # Initialisation du bot avec le fichier de cookies
        bot = Tiktok(cookies=cookie_file)
        
        # Publication de la vidéo via Requests (Signatures Node gérées en interne par le moteur)
        bot.upload_video(
            filename=str(video_path),
            description=description
        )
        
        print(f"✅ Vidéo transmise avec succès à TikTok !")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de l'upload : {e}")
        return False
    finally:
        # Nettoyage du fichier temporaire
        if os.path.exists(cookie_file):
            os.remove(cookie_file)