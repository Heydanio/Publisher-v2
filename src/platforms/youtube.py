"""Upload YouTube via youtube-upload."""
import os
import re
import random
import subprocess
import base64
import tempfile
import shutil
import textwrap
from pathlib import Path
from typing import List

from src.config import AccountConfig
from src.core.safeguards import validate_tags, validate_title, sanitize_content
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_random_description(filepath: str) -> str:
    if not filepath or not os.path.exists(filepath):
        return "Shorts"
    with open(filepath, "r", encoding="utf-8") as f:
        descriptions = [line.strip() for line in f if line.strip()]
    return random.choice(descriptions) if descriptions else "Shorts"


def pick_tags(pool: List[str], min_n: int = 3, max_n: int = 8) -> List[str]:
    if not pool:
        return []
    n = min(random.randint(min_n, max_n), len(pool))
    return random.sample(pool, n)


def _setup_credentials(account_id: str) -> tuple:
    """Decode credentials vers temp dir securise."""
    temp_dir = Path(tempfile.mkdtemp(prefix="yt_creds_"))
    cs_file = temp_dir / f"{account_id}_client_secrets.json"
    creds_file = temp_dir / f"{account_id}_credentials.json"
    
    cs_b64 = os.environ.get("YT_CLIENT_SECRETS_B64", "")
    creds_b64 = os.environ.get("YT_CREDENTIALS_B64", "")
    
    if not cs_b64 or not creds_b64:
        raise ValueError("YT_CLIENT_SECRETS_B64 ou YT_CREDENTIALS_B64 manquant")
    
    cs_file.write_bytes(base64.b64decode(cs_b64))
    creds_file.write_bytes(base64.b64decode(creds_b64))
    return str(cs_file), str(creds_file)


def _cleanup(cs_file: str) -> None:
    """Cleanup credentials temporaires."""
    try:
        parent = Path(cs_file).parent
        if parent.name.startswith("yt_creds_"):
            shutil.rmtree(parent)
    except Exception as e:
        logger.warning(f"Cleanup: {e}")


def upload_to_youtube(config: AccountConfig, video_path: Path, video_name: str) -> bool:
    """Upload YouTube avec validation anti-spam."""
    cs_file = ""
    
    try:
        cs_file, creds_file = _setup_credentials(config.account_id)
        
        # Preparer metadonnees
        desc = sanitize_content(get_random_description(config.content.descriptions_file or ""))
        raw_title = desc.split('#')[0].strip()
        if not raw_title:
            raw_title = f"Video - {config.account_id}"
        title = textwrap.shorten(raw_title, width=95, placeholder="...")
        title = sanitize_content(title)
        
        tags = pick_tags(config.content.tags_pool, 4, 10)
        
        # Validation anti-spam
        valid, reason = validate_title(title, "youtube")
        if not valid:
            logger.error(f"Titre invalide: {reason}")
            return False
        
        valid, reason = validate_tags(tags, "youtube")
        if not valid:
            logger.warning(f"Tags invalides: {reason}. Utilisation d'un set safe.")
            tags = tags[:8]  # Reduire et continuer
        
        category = config.content.youtube_category
        
        logger.info(f"Titre: {title}")
        logger.info(f"Tags: {tags}")
        
        cmd = [
            "youtube-upload",
            "--client-secrets", cs_file,
            "--credentials-file", creds_file,
            "--title", title,
            "--description", desc,
            "--tags", ",".join(tags),
            "--category", category,
            "--privacy", "public",
            str(video_path),
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        logger.info("Upload YouTube reussi")
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
    finally:
        if cs_file:
            _cleanup(cs_file)
