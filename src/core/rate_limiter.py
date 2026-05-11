"""
Rate limiter pour eviter les shadowbans.

Verifie:
- Nombre max d'uploads par jour par compte
- Delai minimum entre 2 uploads
- Distribution sur la journee (pas en rafale)

Base sur la table Supabase 'upload_history'.
"""
from datetime import datetime, timedelta, timezone
from typing import Tuple

from src.core.state import get_supabase_client
from src.utils.logger import get_logger
from src.utils.retry import retry

logger = get_logger(__name__)


# Limites par defaut (peuvent etre override par config)
DEFAULT_LIMITS = {
    "youtube": {
        "max_per_day": 3,
        "min_gap_minutes": 60,  # Minimum 1h entre uploads
        "max_per_hour": 1,
    },
    "tiktok": {
        "max_per_day": 4,
        "min_gap_minutes": 45,  # Minimum 45min entre uploads
        "max_per_hour": 1,
    },
}


@retry(max_attempts=3, initial_delay=1.0)
def record_upload(account_name: str, platform: str) -> None:
    """Enregistre un upload dans l'historique."""
    client = get_supabase_client()
    client.table("upload_history").insert({
        "account_name": account_name,
        "platform": platform,
    }).execute()
    logger.info(f"Upload enregistre: {account_name}/{platform}")


@retry(max_attempts=3, initial_delay=1.0)
def get_recent_uploads(account_name: str, platform: str, hours: int = 24) -> list:
    """Recupere les uploads recents."""
    client = get_supabase_client()
    
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    
    response = (
        client.table("upload_history")
        .select("uploaded_at")
        .eq("account_name", account_name)
        .eq("platform", platform)
        .gte("uploaded_at", since)
        .order("uploaded_at", desc=True)
        .execute()
    )
    
    return response.data or []


def check_rate_limit(
    account_name: str,
    platform: str,
    custom_limits: dict = None
) -> Tuple[bool, str]:
    """
    Verifie si l'upload est autorise par les regles anti-shadowban.
    
    Args:
        account_name: Nom du compte
        platform: youtube ou tiktok
        custom_limits: Override des limites par defaut
    
    Returns:
        Tuple (allowed: bool, reason: str)
    """
    limits = custom_limits or DEFAULT_LIMITS.get(platform, DEFAULT_LIMITS["youtube"])
    
    # Check 1: Uploads dans les dernieres 24h
    uploads_24h = get_recent_uploads(account_name, platform, hours=24)
    
    if len(uploads_24h) >= limits["max_per_day"]:
        return False, (
            f"Limite quotidienne atteinte: {len(uploads_24h)}/{limits['max_per_day']} "
            f"uploads dans les 24h"
        )
    
    # Check 2: Uploads dans la derniere heure
    uploads_1h = get_recent_uploads(account_name, platform, hours=1)
    
    if len(uploads_1h) >= limits["max_per_hour"]:
        return False, (
            f"Limite horaire atteinte: {len(uploads_1h)}/{limits['max_per_hour']} "
            f"uploads dans la derniere heure"
        )
    
    # Check 3: Delai depuis le dernier upload
    if uploads_24h:
        last_upload_str = uploads_24h[0]["uploaded_at"]
        # Parser le timestamp ISO (supabase utilise UTC)
        if last_upload_str.endswith('Z'):
            last_upload_str = last_upload_str.replace('Z', '+00:00')
        elif '+' not in last_upload_str and '-' not in last_upload_str[-6:]:
            last_upload_str += '+00:00'
        
        last_upload = datetime.fromisoformat(last_upload_str)
        time_since_min = (datetime.now(timezone.utc) - last_upload).total_seconds() / 60
        
        if time_since_min < limits["min_gap_minutes"]:
            return False, (
                f"Trop tot apres dernier upload: {time_since_min:.0f}min "
                f"< {limits['min_gap_minutes']}min minimum"
            )
    
    logger.info(
        f"Rate limit OK: {len(uploads_24h)}/{limits['max_per_day']} jour, "
        f"{len(uploads_1h)}/{limits['max_per_hour']} heure"
    )
    return True, "OK"
