import os
import sys
import subprocess
from pathlib import Path
import json
import pickle
import base64

def upload_to_tiktok(config, video_path, video_title):
    current_dir = os.getcwd()
    cli_path = Path("upstream/cli.py")
    
    if not cli_path.exists():
        print(f"❌ Erreur : Le fichier {cli_path} est introuvable. Le clone a échoué.")
        return False

    # --- PRÉPARATION DES COOKIES ---
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    uname = account_id.lower()
    Path("CookiesDir").mkdir(exist_ok=True)
    
    # 🪄 LA MAGIE EST ICI : Conversion JSON -> Pickle
    try:
        # On essaie de lire ton secret comme du JSON
        cookies_json = json.loads(cookies_raw)
        # On le convertit en format binaire Pickle (Ce que Makiisthenes exige)
        cookie_data = pickle.dumps(cookies_json)
        print("✅ Cookies détectés au format JSON et convertis en Pickle pour le moteur.")
    except json.JSONDecodeError:
        # Si ça plante, c'est que c'est l'ancien format Base64 de ton premier script
        try:
            cookie_data = base64.b64decode(cookies_raw.encode("utf-8"))
            print("✅ Cookies détectés au format Base64 et décodés.")
        except Exception as e:
            print(f"❌ Erreur fatale de décodage des cookies : {e}")
            return False

    # Écriture des 3 fichiers vitaux
    (Path("CookiesDir") / f"tiktok_session-{uname}.cookie").write_bytes(cookie_data)
    (Path("CookiesDir") / "main.cookie").write_bytes(cookie_data)
    (Path("CookiesDir") / f"{uname}.cookie").write_bytes(cookie_data)

    # --- PRÉPARATION DE LA COMMANDE ---
    clean_title = video_title.replace(".mp4", "")
    tags = config.get("tags", ["#fyp", "#viral"])
    description = f"{clean_title} {' '.join(tags)}"

    print(f"🚀 [Makiisthenes CLI] Préparation de l'upload : {video_path.name}")
    
    cmd = [
        sys.executable, 
        str(cli_path), 
        "upload", 
        "--user", uname, 
        "-v", str(video_path), 
        "-t", description
    ]
    
    print("RUN:", " ".join(cmd))
    
    # --- EXECUTION ---
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Upload CLI terminé avec succès !")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution du CLI (Code {e.returncode}).")
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
        return False