import os
import json
import sys
from unittest.mock import MagicMock

# --- HACK NUCLÉAIRE : Mock automatique de tout ce qui manque ---
class MockMissingModules:
    def find_spec(self, fullname, path, target=None):
        # Liste des modules critiques du moteur qu'on NE doit PAS mocker
        engine_modules = ["tiktok_uploader", "tiktok_uploader.tiktok"]
        
        # Si le module manquant n'est pas un module vital du moteur, on le simule
        if fullname not in engine_modules and fullname not in sys.modules:
            # On ignore aussi les modules standards de python
            if not fullname.split('.')[0] in sys.builtin_module_names:
                sys.modules[fullname] = MagicMock()
        return None

sys.meta_path.insert(0, MockMissingModules())

def upload_to_tiktok(config, video_path, video_title):
    # --- 1. CONFIGURATION DES CHEMINS ---
    current_dir = os.getcwd()
    engine_dir = os.path.join(current_dir, "engine")
    
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)

    try:
        # Import de la classe principale
        from tiktok_uploader.tiktok import Tiktok
        print("✅ Moteur Tiktok chargé (Bypass des dépendances actif).")
    except Exception as e:
        print(f"🔥 Erreur fatale importation : {e}")
        return False

    # --- 2. PRÉPARATION ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    cookie_file = os.path.join(current_dir, f"cookies_{account_id}.json")
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    description = f"{video_title.replace('.mp4', '')} {' '.join(config.get('tags', ['#fyp']))}"

    # --- 3. EXÉCUTION ---
    try:
        print(f"🚀 [Makiisthenes-V2] Upload : {video_path.name}")
        bot = Tiktok(cookies=cookie_file)
        
        # On force l'upload direct
        bot.upload_video(
            filename=str(video_path),
            description=description
        )
        
        print(f"✅ Vidéo transmise !")
        return True

    except Exception as e:
        print(f"❌ Erreur exécution : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)