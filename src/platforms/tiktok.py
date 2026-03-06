import os
import sys
import subprocess
from pathlib import Path

def upload_to_tiktok(config, video_path, video_title):
    current_dir = os.getcwd()
    
    # On pointe vers le cli.py exactement comme ton ancien code
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

    # Ton ancien script utilisait le nom d'utilisateur. On va utiliser le nom du compte.
    uname = account_id.lower()
    
    # Création du dossier et des fichiers cookies comme dans ton script
    Path("CookiesDir").mkdir(exist_ok=True)
    
    # Si ton secret est en base64 (comme dans ton ancien code), on le décode
    import base64
    try:
        # On teste si c'est du JSON valide
        import json
        json.loads(cookies_raw)
        cookie_data = cookies_raw.encode('utf-8')
    except Exception:
        # Sinon on assume que c'est du base64 comme avant
        cookie_data = base64.b64decode(cookies_raw.encode("utf-8"))

    # On écrit les 3 fichiers que ton script créait pour être sûr à 100% que le CLI le trouve
    (Path("CookiesDir") / f"tiktok_session-{uname}.cookie").write_bytes(cookie_data)
    (Path("CookiesDir") / "main.cookie").write_bytes(cookie_data)
    (Path("CookiesDir") / f"{uname}.cookie").write_bytes(cookie_data)

    # --- PRÉPARATION DE LA COMMANDE ---
    clean_title = video_title.replace(".mp4", "")
    tags = config.get("tags", ["#fyp", "#viral"])
    description = f"{clean_title} {' '.join(tags)}"

    print(f"🚀 [Makiisthenes CLI] Préparation de l'upload : {video_path.name}")
    
    # La commande EXACTE de ton ancien fichier tiktok_runner.py
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
        # On lance le CLI !
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Upload CLI terminé avec succès.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution du CLI (Code {e.returncode}).")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False