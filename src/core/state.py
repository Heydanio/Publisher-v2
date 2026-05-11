"""Gestion de l'etat via Supabase (singleton + retry)."""
from typing import Optional
from supabase import create_client, Client
from src.config import get_required_env
from src.utils.logger import get_logger
from src.utils.retry import retry

logger = get_logger(__name__)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Singleton client Supabase."""
    global _supabase_client
    if _supabase_client is None:
        url = get_required_env("SUPABASE_URL")
        key = get_required_env("SUPABASE_KEY")
        _supabase_client = create_client(url, key)
        logger.info("Client Supabase initialise")
    return _supabase_client


@retry(max_attempts=3, initial_delay=2.0)
def is_video_published(account_name: str, drive_file_id: str, platform: str = "youtube") -> bool:
    """Verifie si video deja publiee."""
    client = get_supabase_client()
    response = (
        client.table("published_videos")
        .select("id")
        .eq("account_name", str(account_name))
        .eq("drive_file_id", str(drive_file_id))
        .eq("platform", str(platform))
        .limit(1)
        .execute()
    )
    return len(response.data) > 0


@retry(max_attempts=3, initial_delay=2.0)
def mark_video_published(account_name: str, drive_file_id: str, platform: str = "youtube") -> None:
    """Marque video comme publiee."""
    client = get_supabase_client()
    client.table("published_videos").insert({
        "account_name": account_name,
        "drive_file_id": drive_file_id,
        "platform": platform,
    }).execute()
    logger.info(f"Video {drive_file_id} marquee publiee sur {platform}")
