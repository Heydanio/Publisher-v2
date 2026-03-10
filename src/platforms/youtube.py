import os
import re
import random
import subprocess
import base64
from pathlib import Path

TITLE_MAX = 100

def sanitize_title(name: str) -> str:
    """Nettoie le nom du fichier pour en faire un beau titre YouTube."""
    name_no_ext = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", name)
    title = re.sub(r"\s+", " ", name_no_ext).strip()
    if len(title) > TITLE_MAX:
        title = title[:TITLE_MAX-1] + "…"
    return title

def get_random_description(filepath: str) -> str:
    """Pioche une description au hasard dans ton fichier texte."""
    if not os.path.exists(filepath):
        return "Shorts 🔥"
    with open(filepath, "r", encoding="utf-8") as f:
        descriptions = [line.strip() for line in f if line.strip()]
    return random.choice(descriptions) if descriptions else "Shorts 🔥"

def pick_tags(pool: list, min_n=3, max_n=8) -> list:
    """Pioche des tags au hasard dans le pool."""
    n = random.randint(min_n, max_n)
    n = min(n, len(pool))
    return random.sample(pool, n)

def upload_to_youtube(config: dict, video_path: Path, video_name: str) -> bool:
    """Gère tout le processus d'upload vers YouTube."""
    account_id = config["account_id"]
    
    # 1. Gestion des fichiers de connexion (Local ou GitHub)
    os.makedirs("secrets", exist_ok=True)
    client_secrets_file = f"secrets/{account_id}_client_secrets.json"
    credentials_file = f"secrets/{account_id}_credentials.json"

    # Récupération depuis les variables d'environnement (pour GitHub Actions)
    yt_secrets_b64 = os.environ.get("YT_CLIENT_SECRETS_B64")
    yt_creds_b64 = os.environ.get("YT_CREDENTIALS_B64")

    if yt_secrets_b64:
        with open(client_secrets_file, "wb") as f:
            f.write(base64.b64decode(yt_secrets_b64))
    
    if yt_creds_b64:
        with open(credentials_file, "wb") as f:
            f.write(base64.b64decode(yt_creds_b64))

    # 2. Vérification finale de l'existence des fichiers
    if not os.path.exists(client_secrets_file):
        print(f"❌ Erreur : Fichier client_secrets introuvable pour {account_id}.")
        return False

    # 3. Préparation des métadonnées
    desc_file = config["content"]["descriptions_file"]
    desc = get_random_description(desc_file)
    
    # --- NOUVEAU TITRE INTELLIGENT ---
    # On prend la description et on coupe au premier '#' pour garder juste l'accroche
    raw_title = desc.split('#')[0].strip()
    
    # Si par malheur la phrase est vide, on met un titre de secours
    if not raw_title:
        raw_title = "Un dossier incroyable ! 😱"
        
    # Sécurité : YouTube limite les titres à 100 caractères
    if len(raw_title) > 95:
        title = raw_title[:95] + "..."
    else:
        title = raw_title
    # ---------------------------------

    tags_pool = config["content"]["tags_pool"]
    tags = pick_tags(tags_pool, 4, 10)
    category = config["content"].get("youtube_category", "Entertainment")
    
    print("\n" + "="*30)
    print(f"📝 Titre: {title}")
    print(f"📝 Description: {desc}")
    print(f"🏷️ Tags: {', '.join(tags)}")
    print("="*30 + "\n")

    # 4. Lancement de youtube-upload
    cmd = [
        "youtube-upload",
        "--client-secrets", client_secrets_file,
        "--credentials-file", credentials_file,
        "--title", title,
        "--description", desc,
        "--tags", ",".join(tags),
        "--category", category,
        "--privacy", "public",
        str(video_path)
    ]

    print("🚀 RUN: Lancement de youtube-upload...")
    try:
        subprocess.run(cmd, check=True)
        print("✅ Upload YouTube terminé avec succès !")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec de l'upload YouTube: {e}")
        return False