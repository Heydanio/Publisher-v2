import os
import json
import sys
import importlib.util
from unittest.mock import MagicMock

# --- HACK DE SURVIE : On simule les modules manquants ---
# Cela empêche les erreurs "ModuleNotFoundError" au chargement du moteur
for module_name in ["moviepy", "moviepy.editor", "undetected_chromedriver"]:
    if module_name not in sys.path:
        sys.modules[module_name] = MagicMock()

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. CONFIGURATION DES CHEMINS ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    # Ajout du moteur au chemin système pour que Python le trouve
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)

    try:
        # Import de la classe principale du moteur Makiisthenes
        from tiktok_uploader.tiktok import Tiktok
        print("✅ Moteur Tiktok (v2.0 Class) chargé avec succès.")
    except Exception as e:
        print(f"🔥 Erreur fatale lors du chargement de la classe Tiktok : {e}")
        return False

    # --- 2. PRÉPARATION DES COOKIES ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    # Le moteur a besoin d'un fichier physique pour lire les cookies
    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    # Préparation de la légende (Titre + Tags)
    clean_title = video_title.replace(".mp4", "")
    tags = config.get("tags", ["#fyp", "#viral"])
    description = f"{clean_title} {' '.join(tags)}"

    # --- 3. EXÉCUTION DE L'UPLOAD ---
    try:
        print(f"🚀 [Makiisthenes-V2] Début de l'upload : {video_path.name}")
        
        # Initialisation du bot avec le fichier de cookies
        bot = Tiktok(cookies=cookie_file)
        
        # Publication de la vidéo
        # Le moteur va appeler automatiquement le script Node.js pour la signature
        bot.upload_video(
            filename=str(video_path),
            description=description
        )
        
        print(f"✅ Succès : La vidéo '{video_title}' a été transmise à TikTok !")
        return True

    except Exception as e:
        print(f"❌ Erreur pendant l'upload réel : {e}")
        return False
    finally:
        # Nettoyage : On supprime le fichier de cookies après usage
        if os.path.exists(cookie_file):
            os.remove(cookie_file)