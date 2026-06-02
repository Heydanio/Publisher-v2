"""Upload YouTube 2026 via googleapiclient (sans youtube-upload CLI)."""
import os
import sys
import base64
import tempfile
import time
import random
from pathlib import Path
from src.config import AccountConfig
from src.core.safeguards import (
    sanitize_content,
    run_full_validation,
)
from src.core.anti_shadowban import (
    generate_varied_description,
    randomize_tag_order,
)
from src.utils.humanizer import humanize_description
from src.utils.logger import get_logger

logger = get_logger(__name__)

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"


def _prepare_credentials(account_name: str):
    """Charge et rafraîchit les credentials OAuth2 YouTube."""
    import json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    client_secrets_b64 = os.environ.get("YT_CLIENT_SECRETS_B64")
    if not client_secrets_b64:
        raise RuntimeError("YT_CLIENT_SECRETS_B64 manquant")

    if account_name == "youtube_compte2":
        creds_b64 = os.environ.get("YT_CREDENTIALS_COMPTE2_B64")
    else:
        creds_b64 = os.environ.get("YT_CREDENTIALS_B64")

    if not creds_b64:
        raise RuntimeError(f"Credentials manquants pour {account_name}")

    client_secrets = json.loads(base64.b64decode(client_secrets_b64))
    creds_data = json.loads(base64.b64decode(creds_b64))

    web_or_installed = client_secrets.get("web") or client_secrets.get("installed", {})
    client_id = web_or_installed.get("client_id")
    client_secret = web_or_installed.get("client_secret")
    token_uri = web_or_installed.get("token_uri", "https://oauth2.googleapis.com/token")

    # Supporte format oauth2client (access_token) ET google-auth (token)
    access_token = creds_data.get("token") or creds_data.get("access_token")
    refresh_token = creds_data.get("refresh_token")

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=[YOUTUBE_UPLOAD_SCOPE],
    )

    if creds.expired or not creds.valid:
        logger.info("Refresh token OAuth2...")
        creds.refresh(Request())

    youtube = build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=creds)
    return youtube


def _load_descriptions_pool(file_path: str) -> list:
    """Charge la pool de descriptions depuis un fichier."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Fichier descriptions introuvable: {path}")
        return []
    content = path.read_text(encoding='utf-8')
    return [d.strip() for d in content.split('\n\n') if d.strip()]


def _upload_with_resumable(youtube, video_path: Path, title: str, description: str,
                           tags: list, category_id: str, privacy: str = "public") -> str | None:
    """Upload via resumable upload API. Retourne video_id ou None."""
    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": [t.lstrip("#") for t in tags[:15]],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/*",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    retry_count = 0
    max_retries = 5
    retriable_exceptions = (Exception,)
    retriable_status_codes = [500, 502, 503, 504]

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                logger.info(f"Upload: {pct}%")
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                raise
            wait = (2 ** retry_count) + random.random()
            logger.warning(f"Erreur upload chunk, retry {retry_count}/{max_retries} dans {wait:.1f}s: {e}")
            time.sleep(wait)

    return response.get("id")


CATEGORY_IDS = {
    "Entertainment": "24",
    "Gaming": "20",
    "Music": "10",
    "Howto & Style": "26",
    "People & Blogs": "22",
    "Science & Technology": "28",
    "Sports": "17",
    "Film & Animation": "1",
}


def upload_to_youtube(
    config: AccountConfig,
    video_path: Path,
    video_title: str,
    account_name: str = None
) -> bool:
    """Upload YouTube avec validation anti-shadowban 2026."""

    acc_name = account_name or config.account_name

    # === VALIDATION ANTI-SHADOWBAN 2026 ===
    clean_title = sanitize_content(video_title.replace(".mp4", "").replace(".mov", "").replace(".MP4", ""))

    tags_pool = config.content.tags_pool if hasattr(config.content, 'tags_pool') else []
    randomized_tags = randomize_tag_order(tags_pool[:15], seed=video_path.name)

    validation = run_full_validation(
        platform="youtube",
        title=clean_title,
        tags=randomized_tags,
        description=clean_title,
        video_path=video_path,
        recent_titles=[]
    )

    if not validation["valid"]:
        logger.error("Upload BLOQUE par safeguards 2026")
        for err in validation["errors"]:
            logger.error(f"  {err}")
        return False

    # === DESCRIPTION ===
    descriptions_pool = []
    if hasattr(config.content, 'descriptions_file') and config.content.descriptions_file:
        descriptions_pool = _load_descriptions_pool(config.content.descriptions_file)

    if descriptions_pool:
        import random as _random
        _random.seed(video_path.name)
        base_description = _random.choice(descriptions_pool)
        _random.seed()
    else:
        base_description = generate_varied_description(
            title=clean_title,
            tags=randomized_tags,
            seed=video_path.name
        )

    description = humanize_description(base_description, seed=video_path.name)

    # === CATEGORY ===
    category_name = "Entertainment"
    if hasattr(config.content, 'youtube_category') and config.content.youtube_category:
        category_name = config.content.youtube_category
    category_id = CATEGORY_IDS.get(category_name, "24")

    # === TITRE FINAL ===
    # Si le titre est vide ou juste des hashtags, utiliser le nom du fichier nettoyé
    title_for_upload = clean_title if len(clean_title.replace("#", "").strip()) > 3 else video_path.stem

    logger.info(f"Upload YouTube: {video_path.name}")
    logger.info(f"Titre: {title_for_upload[:60]}")

    # === UPLOAD VIA API ===
    try:
        youtube = _prepare_credentials(acc_name)
    except Exception as e:
        logger.error(f"Credentials: {e}")
        return False

    try:
        video_id = _upload_with_resumable(
            youtube=youtube,
            video_path=video_path,
            title=title_for_upload,
            description=description,
            tags=randomized_tags,
            category_id=category_id,
            privacy="public",
        )
        if video_id:
            logger.info(f"Upload YouTube reussi: https://youtu.be/{video_id}")
            return True
        else:
            logger.error("Upload retourne None — pas de video_id")
            return False
    except Exception as e:
        logger.error(f"Upload echec: {e}")
        return False
