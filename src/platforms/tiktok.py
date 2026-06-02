"""Upload TikTok 2026 avec safeguards complets."""
import os
import sys
import subprocess
import json
import pickle
import base64
import shutil
from pathlib import Path
from src.config import AccountConfig
from src.core.safeguards import (
    validate_tags, 
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


def _prepare_cookies(account_id: str) -> bool:
    """Prépare les cookies depuis le fichier du workflow ou env."""
    Path("CookiesDir").mkdir(exist_ok=True)
    
    # Le workflow crée le fichier dans upstream/CookiesDir
    source = Path("upstream/CookiesDir/tiktok_session-tiktok_1.cookie")
    if source.exists():
        uname = account_id.lower().replace("@", "")
        dest = Path("CookiesDir") / f"tiktok_session-{uname}.cookie"
        shutil.copy(source, dest)
        logger.info(f"Cookie copie depuis workflow: {dest}")
        return True
    
    # Fallback: env
    cookies_raw = os.environ.get("TIKTOK_COOKIES_TIKTOK_1")
    if not cookies_raw:
        logger.error("Cookies manquants (ni fichier ni env)")
        return False
    
    cookie_data = None
    try:
        cookie_data = base64.b64decode(cookies_raw.encode("utf-8"))
        logger.info("Cookies base64 decodes")
    except Exception:
        try:
            cookies_json = json.loads(cookies_raw)
            cookie_data = pickle.dumps(cookies_json)
            logger.info("Cookies JSON convertis en pickle")
        except Exception as e:
            logger.error(f"Decodage cookies: {e}")
            return False
    
    if not cookie_data:
        return False
    
    uname = account_id.lower().replace("@", "")
    for filename in [f"tiktok_session-{uname}.cookie", "main.cookie", f"{uname}.cookie"]:
        (Path("CookiesDir") / filename).write_bytes(cookie_data)
    
    return True


def upload_to_tiktok(
    config: AccountConfig, 
    video_path: Path, 
    video_title: str,
    account_name: str = None
) -> bool:
    """Upload TikTok avec validation anti-shadowban 2026."""
    cli_path = Path("upstream/cli.py")
    if not cli_path.exists():
        logger.error(f"CLI introuvable: {cli_path}")
        return False
    
    if not _prepare_cookies(config.account_id):
        return False
    
    # === VALIDATION ANTI-SHADOWBAN 2026 ===
    clean_title = sanitize_content(video_title.replace(".mp4", "").replace(".MP4", "").replace(".mov", "").replace(".MOV", ""))
    
    # Randomize tag order pour casser pattern
    randomized_tags = randomize_tag_order(config.tags, seed=video_path.name)
    
    validation = run_full_validation(
        platform="tiktok",
        title=clean_title,
        tags=randomized_tags,
        description=clean_title,
        video_path=video_path,
        recent_titles=[]
    )
    
    if not validation["valid"]:
        logger.error("🛑 Upload BLOQUÉ par les safeguards 2026")
        for err in validation["errors"]:
            logger.error(f"  {err}")
        return False
    
    # === GÉNÉRATION DESCRIPTION VARIÉE ===
    description = generate_varied_description(
        title=clean_title,
        tags=randomized_tags,
        seed=video_path.name
    )
    
    # Humanize (anti-LLM detection)
    description = humanize_description(description, seed=video_path.name)
    
    uname = config.account_id.lower().replace("@", "")
    
    cmd = [
        sys.executable, str(cli_path), "upload",
        "--user", uname, "-v", str(video_path), "-t", description,
    ]
    
    logger.info(f"📤 Upload TikTok: {video_path.name}")
    logger.info(f"📝 Description: {description[:80]}...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=900)
        logger.info("✅ Upload TikTok reussi")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Upload timeout (15min)")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Upload echec (code {e.returncode})")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr[:500]}")
        return False
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return False
