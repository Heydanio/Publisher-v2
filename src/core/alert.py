"""Notifications Discord avec embeds riches - 3 couleurs TITAN V3."""
import os
from typing import Optional, Dict, Any
import requests
from src.utils.logger import get_logger
from src.utils.retry import retry

logger = get_logger(__name__)


def _webhook() -> Optional[str]:
    return os.environ.get("DISCORD_WEBHOOK_URL")


@retry(max_attempts=3, initial_delay=1.0)
def _send(payload: Dict[str, Any]) -> bool:
    url = _webhook()
    if not url:
        logger.warning("Pas de webhook Discord")
        return False
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.status_code == 204


def send_discord_notification(message: str) -> bool:
    """Notification simple."""
    try:
        return _send({"content": message})
    except Exception as e:
        logger.error(f"Discord echec: {e}")
        return False


def send_success_notification(platform: str, account_id: str, video_name: str, time_str: str) -> bool:
    """🟢 GREEN - Notification de succès avec embed."""
    colors = {"youtube": 0xFF0000, "tiktok": 0x000000}
    embed = {
        "title": f"✅ Publication réussie - {platform.upper()}",
        "color": 0x00FF00,  # GREEN
        "fields": [
            {"name": "Compte", "value": account_id, "inline": True},
            {"name": "Plateforme", "value": platform.upper(), "inline": True},
            {"name": "Heure", "value": time_str, "inline": True},
            {"name": "Video", "value": f"`{video_name[:200]}`", "inline": False},
        ],
        "footer": {"text": "Publisher-v2 TITAN V3 | ✅ SUCCESS"},
    }
    try:
        return _send({"embeds": [embed]})
    except Exception as e:
        logger.error(f"Notification echec: {e}")
        return False


def send_error_notification(platform: str, account_id: str, error_message: str) -> bool:
    """🔴 RED - Notification d'erreur (vraie erreur)."""
    embed = {
        "title": f"❌ Erreur - {platform.upper()}",
        "color": 0xFF0000,  # RED
        "fields": [
            {"name": "Compte", "value": account_id, "inline": True},
            {"name": "Erreur", "value": f"```{error_message[:1000]}```", "inline": False},
        ],
        "footer": {"text": "Publisher-v2 TITAN V3 | ❌ ERROR"},
    }
    try:
        return _send({"embeds": [embed]})
    except Exception as e:
        logger.error(f"Notification echec: {e}")
        return False


def send_rate_limit_notification(platform: str, account_id: str, reason: str) -> bool:
    """🟠 ORANGE - Notification de rate limit (semi-succès, pas d'upload mais workflow OK)."""
    embed = {
        "title": f"⏸️ Rate Limit - {platform.upper()}",
        "color": 0xFFA500,  # ORANGE
        "description": "Upload reporté pour éviter shadowban - Workflow SUCCESS",
        "fields": [
            {"name": "Compte", "value": account_id, "inline": True},
            {"name": "Raison", "value": reason, "inline": False},
        ],
        "footer": {"text": "Publisher-v2 TITAN V3 | ⏸️ RATE_LIMITED"},
    }
    try:
        return _send({"embeds": [embed]})
    except Exception as e:
        logger.error(f"Notification echec: {e}")
        return False
