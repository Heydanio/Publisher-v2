import os
import json
import sys

# On force l'ajout du chemin interne du moteur
engine_path = os.path.join(os.getcwd(), "engine")
if engine_path not in sys.path:
    sys.path.append(engine_path)

try:
    from tiktok_uploader.uploader import upload_video
except ImportError as e:
    print(f"❌ Erreur d'importation du moteur : {e}")
    # On tente un import relatif si le premier échoue
    from engine.tiktok_uploader.uploader import upload_video

def upload_to_tiktok(config, video_path, video_title):
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    # Le moteur a besoin d'un fichier physique
    cookie_file = f"cookies_{account_id}.json"
    with open(cookie_file, 'w') as f:
        f.write(cookies_raw)

    print(f"🚀 [Makiisthenes-Engine] Lancement de l'upload réel...")
    
    tags = config.get("tags", ["#fyp"])
    description = f"{video_title.replace('.mp4', '')} {' '.join(tags)}"

    try:
        # APPEL DU VRAI MOTEUR
        # success est True si la vidéo est postée
        success = upload_video(
            filename=str(video_path),
            description=description,
            cookies=cookie_file
        )
        
        if success:
            print(f"✅ TikTok : Publication réussie !")
            return True
        else:
            print(f"❌ L'upload a échoué (Vérifie les logs Node.js ou les cookies)")
            return False
            
    except Exception as e:
        print(f"🔥 Erreur moteur : {e}")
        return False
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)