"""Upload YouTube 2026 avec safeguards complets."""
import os
import sys
import subprocess
import base64
import tempfile
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


def _prepare_credentials(account_name: str) -> tuple:
    """
    Prépare les credentials YouTube depuis env.
    
    Returns:
        (client_secrets_path, credentials_path)
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="yt_"))
    
    # Client secrets (commun)
    client_secrets_b64 = os.environ.get("YT_CLIENT_SECRETS_B64")
    if not client_secrets_b64:
        raise RuntimeError("YT_CLIENT_SECRETS_B64 manquant")
    
    cs_path = tmp_dir / "client_secrets.json"
    cs_path.write_bytes(base64.b64decode(client_secrets_b64))
    
    # Credentials (par compte)
    if account_name == "youtube_compte2":
        creds_b64 = os.environ.get("YT_CREDENTIALS_COMPTE2_B64")
    else:
        creds_b64 = os.environ.get("YT_CREDENTIALS_B64")
    
    if not creds_b64:
        raise RuntimeError(f"Credentials manquants pour {account_name}")
    
    creds_path = tmp_dir / ".youtube-upload-credentials.json"
    creds_path.write_bytes(base64.b64decode(creds_b64))
    
    return cs_path, creds_path


def _load_descriptions_pool(file_path: str) -> list:
    """Charge la pool de descriptions depuis un fichier."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Fichier descriptions introuvable: {path}")
        return []
    
    content = path.read_text(encoding='utf-8')
    # Split par double newline ou par marker "---"
    descriptions = [d.strip() for d in content.split('\n\n') if d.strip()]
    return descriptions


def upload_to_youtube(
    config: AccountConfig,
    video_path: Path,
    video_title: str,
    account_name: str = None
) -> bool:
    """Upload YouTube avec validation anti-shadowban 2026."""
    
    acc_name = account_name or config.account_name
    
    # === VALIDATION ANTI-SHADOWBAN 2026 ===
    clean_title = sanitize_content(video_title.replace(".mp4", "").replace(".mov", ""))
    
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
        logger.error("🛑 Upload BLOQUÉ par les safeguards 2026")
        for err in validation["errors"]:
            logger.error(f"  {err}")
        return False
    
    # === DESCRIPTION VARIÉE ===
    descriptions_pool = []
    if hasattr(config.content, 'descriptions_file'):
        descriptions_pool = _load_descriptions_pool(config.content.descriptions_file)
    
    if descriptions_pool:
        import random
        random.seed(video_path.name)
        base_description = random.choice(descriptions_pool)
        random.seed()
    else:
        base_description = generate_varied_description(
            title=clean_title,
            tags=randomized_tags,
            seed=video_path.name
        )
    
    description = humanize_description(base_description, seed=video_path.name)
    
    # === CREDENTIALS ===
    try:
        cs_path, creds_path = _prepare_credentials(acc_name)
    except Exception as e:
        logger.error(f"Credentials: {e}")
        return False
    
    # === COMMAND ===
    category = "Entertainment"
    if hasattr(config.content, 'youtube_category'):
        category = config.content.youtube_category
    
    cmd = [
        "youtube-upload",
        "--title", clean_title[:100],
        "--description", description[:5000],
        "--category", category,
        "--tags", ",".join([t.lstrip("#") for t in randomized_tags[:15]]),
        "--client-secrets", str(cs_path),
        "--credentials-file", str(creds_path),
        "--privacy", "public",
        str(video_path),
    ]
    
    logger.info(f"📤 Upload YouTube: {video_path.name}")
    logger.info(f"📝 Titre: {clean_title[:60]}")
    
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, timeout=1200
        )
        logger.info("✅ Upload YouTube réussi")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Upload timeout (20min)")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Upload échec (code {e.returncode})")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr[:500]}")
        return False
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return False
