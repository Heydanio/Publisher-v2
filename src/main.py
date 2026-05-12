"""Publisher-v2 TITAN COLOSSAL V3 - Point d'entree avec safeguards 2026."""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from src.config import load_account_config, AccountConfig
from src.core.state import mark_video_published
from src.core.drive import get_unpublished_video, download_video
from src.core.alert import (
    send_success_notification,
    send_error_notification,
    send_rate_limit_notification,
)
from src.core.rate_limiter import check_rate_limit, record_upload
from src.platforms.youtube import upload_to_youtube
from src.platforms.tiktok import upload_to_tiktok
from src.utils.logger import get_logger
from src.utils.timing import human_delay, get_jittered_upload_time

# Nouveau: anti-shadowban 2026
from src.core.anti_shadowban import (
    get_frequency_rules,
    is_publishing_window,
)
from src.core.ip_quality import check_ip_quality_now

logger = get_logger(__name__)
PARIS_TZ = ZoneInfo("Europe/Paris")


def _sanitize_filename(name: str) -> str:
    safe_chars = (' ', '.', '_', '-')
    return "".join(c for c in name if c.isalnum() or c in safe_chars).strip()


def _upload_video(config: AccountConfig, video_path: Path, video_name: str, account_name: str) -> bool:
    if config.platform == "youtube":
        return upload_to_youtube(config, video_path, video_name, account_name)
    elif config.platform == "tiktok":
        return upload_to_tiktok(config, video_path, video_name, account_name)
    return False


def run_publisher(account_name: str) -> bool:
    """Pipeline complet TITAN V3."""
    logger.info("=" * 80)
    logger.info(f"🚀 TITAN V3 - Compte: {account_name}")
    logger.info("=" * 80)
    
    # 1. Config
    try:
        config = load_account_config(account_name)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Config: {e}")
        return False
    
    # 2. Heure
    now = datetime.now(PARIS_TZ)
    time_str = now.strftime("%Hh%M")
    logger.info(f"⏰ Heure Paris: {time_str}")
    
    # 3. NOUVEAU 2026: Check IP quality
    ip_check = check_ip_quality_now(strict=False)
    if ip_check.get("warning"):
        logger.warning(f"🌐 {ip_check['warning']}")
    
    # 4. Check rate limit ANTI-SHADOWBAN
    limits = config.get_rate_limits()
    
    # Override avec règles 2026 si plus strictes
    rules_2026 = get_frequency_rules(config.platform)
    limits_2026 = {
        "max_per_day": min(limits.get("max_per_day", 999), rules_2026["max_per_day"]),
        "min_gap_minutes": max(limits.get("min_gap_minutes", 0), rules_2026["min_gap_minutes"]),
        "max_per_hour": min(limits.get("max_per_hour", 999), rules_2026["max_per_hour"]),
    }
    logger.info(f"📊 Limits 2026: {limits_2026}")
    
    allowed, reason = check_rate_limit(account_name, config.platform, limits_2026)
    
    if not allowed:
        logger.warning(f"🛑 Rate limit: {reason}")
        send_rate_limit_notification(config.platform, config.account_id, reason)
        return False
    
    # 5. Force post check
    force_post = os.environ.get("FORCE_POST") == "1"
    if not force_post:
        if not config.schedule.is_publishing_time(now.hour, now.minute):
            logger.info(f"⏱️ Hors plage: slots={config.schedule.slots_hours}")
            return False
    
    logger.info(f"🎯 Mode publication: {config.platform}/{config.account_id}")
    
    # 6. Chercher video
    video = get_unpublished_video(
        account_name=account_name,
        folder_ids=config.drive_folder_ids,
        platform=config.platform,
    )
    
    if not video:
        logger.info("📭 Aucune video disponible")
        return False
    
    video_name = video["name"]
    video_id = video["id"]
    logger.info(f"🎬 Video: {video_name}")
    
    # 7. Pause humanisation (avec jitter amélioré)
    if os.environ.get("HUMAN_DELAY") == "1":
        human_delay(base_seconds=120, variance=0.5)
    
    # 8. Download
    tmp_dir = Path(tempfile.mkdtemp(prefix="publisher_"))
    
    try:
        safe_name = _sanitize_filename(video_name)
        local_path = tmp_dir / safe_name
        download_video(video_id, local_path)
        
        # 9. Upload (avec validation 2026 dans la plateforme)
        success = _upload_video(config, local_path, video_name, account_name)
        
        # 10. Finaliser
        if success:
            try:
                mark_video_published(account_name, video_id, config.platform)
            except Exception as e:
                logger.error(f"Supabase down après upload: {e}")
            
            try:
                record_upload(account_name, config.platform)
            except Exception as e:
                logger.warning(f"Rate history fail: {e}")
            
            send_success_notification(config.platform, config.account_id, video_name, time_str)
            return True
        else:
            send_error_notification(config.platform, config.account_id, "Upload échoué (safeguards 2026 ou erreur)")
            return False
    
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> int:
    account_name = os.environ.get("ACCOUNT_NAME", "youtube_compte1")
    try:
        success = run_publisher(account_name)
        return 0 if success else 1
    except Exception as e:
        logger.critical(f"💀 Fatal: {e}", exc_info=True)
        try:
            send_error_notification("system", account_name, str(e))
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
