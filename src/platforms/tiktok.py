"""Upload TikTok (utilise fork heydanio/TiktokAutoUploader)."""
import os
import sys
import subprocess
import json
import pickle
import base64
from pathlib import Path

from src.config import AccountConfig
from src.core.safeguards import validate_tags, sanitize_content
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _prepare_cookies(account_id: str) -> bool:
    """Prepare les cookies depuis env."""
    account_upper = account_id.upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_upper}")
    
    if not cookies_raw:
        logger.error(f"TIKTOK_COOKIES_{account_upper} manquant")
        return False
    
    uname = account_id.lower()
    Path("CookiesDir").mkdir(exist_ok=True)
    
    cookie_data = None
    try:
        cookies_json = json.loads(cookies_raw)
        cookie_data = pickle.dumps(cookies_json)
        logger.info("Cookies JSON convertis en pickle")
    except json.JSONDecodeError:
        try:
            cookie_data = base64.b64decode(cookies_raw.encode("utf-8"))
            logger.info("Cookies base64 decodes")
        except Exception as e:
            logger.error(f"Decodage cookies: {e}")
            return False
    
    if not cookie_data:
        return False
    
    for filename in [f"tiktok_session-{uname}.cookie", "main.cookie", f"{uname}.cookie"]:
        (Path("CookiesDir") / filename).write_bytes(cookie_data)
    
    return True


def upload_to_tiktok(config: AccountConfig, video_path: Path, video_title: str) -> bool:
    """Upload TikTok."""
    cli_path = Path("upstream/cli.py")
    
    if not cli_path.exists():
        logger.error(f"CLI introuvable: {cli_path}")
        return False
    
    if not _prepare_cookies(config.account_id):
        return False
    
    # Validation tags
    valid, reason = validate_tags(config.tags, "tiktok")
    if not valid:
        logger.warning(f"Tags problematiques: {reason}")
    
    clean_title = sanitize_content(video_title.replace(".mp4", "").replace(".mov", ""))
    tags_str = " ".join(config.tags[:5])  # Max 5 tags TikTok pour eviter spam
    description = f"{clean_title} {tags_str}"
    
    uname = config.account_id.lower()
    cmd = [
        sys.executable, str(cli_path), "upload",
        "--user", uname, "-v", str(video_path), "-t", description,
    ]
    
    logger.info(f"Upload TikTok: {video_path.name}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=900)
        logger.info("Upload TikTok reussi")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Upload timeout")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Upload echec (code {e.returncode})")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr[:500]}")
        return False
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return False
