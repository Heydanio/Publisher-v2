"""Client Google Drive avec pagination."""
import io
import re
import json
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

from src.core.state import is_video_published
from src.config import get_required_env
from src.utils.logger import get_logger
from src.utils.retry import retry

logger = get_logger(__name__)
_drive_service: Optional[Any] = None


def _parse_sa_json(encoded: str) -> Dict[str, Any]:
    """Parse le JSON du service account."""
    decoded = base64.b64decode(encoded).decode('utf-8').strip()
    match = re.search(r'(\{.*\})', decoded, re.DOTALL)
    if match:
        decoded = match.group(1)
    return json.loads(decoded)


def get_drive_service() -> Any:
    """Singleton du service Drive."""
    global _drive_service
    if _drive_service is None:
        encoded = get_required_env("GDRIVE_SA_JSON_B64").strip()
        sa_info = _parse_sa_json(encoded)
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        _drive_service = build('drive', 'v3', credentials=creds)
        logger.info("Service Drive initialise")
    return _drive_service


@retry(max_attempts=3, initial_delay=2.0)
def _list_videos(folder_id: str) -> List[Dict[str, str]]:
    """Liste TOUTES les videos d'un dossier (paginated)."""
    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"
    
    all_videos: List[Dict[str, str]] = []
    page_token: Optional[str] = None
    
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, createdTime)",
            orderBy="createdTime",
            pageSize=1000,
            pageToken=page_token,
        ).execute()
        
        all_videos.extend(response.get('files', []))
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    
    return all_videos


_BATCH_FETCH_FAILED = object()  # sentinel


def _get_published_ids_batch(account_name: str, platform: str):
    """
    Recupere tous les drive_file_id deja publies en une requete.
    Retourne un set, ou _BATCH_FETCH_FAILED si erreur.
    """
    from src.core.state import get_supabase_client
    try:
        client = get_supabase_client()
        # Supabase default limit = 1000. range() pour paginer si besoin.
        all_ids: set = set()
        offset = 0
        page_size = 1000
        while True:
            response = (
                client.table("published_videos")
                .select("drive_file_id")
                .eq("account_name", account_name)
                .eq("platform", platform)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            rows = response.data or []
            all_ids.update(row["drive_file_id"] for row in rows)
            if len(rows) < page_size:
                break
            offset += page_size
        logger.info(f"IDs publies en cache: {len(all_ids)}")
        return all_ids
    except Exception as e:
        logger.warning(f"Batch fetch publie echec, fallback une-par-une: {e}")
        return _BATCH_FETCH_FAILED


def get_unpublished_video(
    account_name: str,
    folder_ids: List[str],
    platform: str = "youtube"
) -> Optional[Dict[str, str]]:
    """Trouve la premiere video non publiee (batch Supabase check)."""
    service = get_drive_service()

    # 1 requete Supabase pour tous les IDs publies
    batch = _get_published_ids_batch(account_name, platform)
    batch_ok = batch is not _BATCH_FETCH_FAILED

    for folder_id in folder_ids:
        logger.info(f"Scan dossier: {folder_id}")

        try:
            folder_info = service.files().get(fileId=folder_id, fields="name").execute()
            logger.info(f"Dossier: {folder_info.get('name')}")
        except Exception as e:
            logger.error(f"Acces dossier {folder_id} echec: {e}")
            continue

        try:
            videos = _list_videos(folder_id)
            logger.info(f"Videos trouvees: {len(videos)}")
        except Exception as e:
            logger.error(f"Scan {folder_id} echec: {e}")
            continue

        for video in videos:
            vid_id = video['id']
            if batch_ok:
                if vid_id in batch:
                    logger.debug(f"Deja publiee: {video['name']}")
                    continue
            else:
                # Fallback: check individuel (lent mais fiable)
                if is_video_published(account_name, vid_id, platform):
                    logger.debug(f"Deja publiee: {video['name']}")
                    continue
            logger.info(f"Match: {video['name']}")
            return video

    logger.info("Aucune video disponible")
    return None


@retry(max_attempts=3, initial_delay=5.0)
def download_video(file_id: str, local_path: Path) -> Path:
    """Telecharge une video."""
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    
    with io.FileIO(local_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=10 * 1024 * 1024)
        logger.info(f"Telechargement: {file_id}")
        done = False
        while not done:
            status, done = downloader.next_chunk()
    
    size_mb = local_path.stat().st_size / (1024 * 1024)
    logger.info(f"Telecharge: {size_mb:.1f} MB")
    return local_path
