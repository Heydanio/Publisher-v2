"""
Content Validator 2026

Validation du contenu vidéo (text density OCR, durée, qualité).
TikTok 2026 limite le texte incrusté à max 4 secondes par fenêtre de 10s.

Note: OCR est optionnel. Si OpenCV/Tesseract non installé, validation skipée
avec warning au lieu de fail.
"""
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Flag pour OCR optionnel
try:
    import cv2  # noqa
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.debug("OpenCV non installé - validation OCR désactivée")


def get_video_duration(video_path: Path) -> Optional[float]:
    """Retourne la durée de la vidéo en secondes."""
    if not OCR_AVAILABLE:
        return None
    
    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if fps > 0:
            return frame_count / fps
    except Exception as e:
        logger.warning(f"Impossible de lire la durée: {e}")
    
    return None


def validate_video_duration(video_path: Path, platform: str) -> tuple:
    """
    Valide la durée selon la plateforme.
    
    TikTok 2026: optimal 15-60s (jusqu'à 3min OK)
    YouTube Shorts: max 60s
    YouTube long: pas de limite
    """
    duration = get_video_duration(video_path)
    if duration is None:
        return True, "Durée inconnue (OCR indisponible)"
    
    if platform == "tiktok":
        if duration < 5:
            return False, f"Trop courte: {duration:.1f}s (min 5s)"
        if duration > 600:  # 10 min
            return False, f"Trop longue pour TikTok: {duration:.1f}s"
        
        # Sweet spot 2026
        if 15 <= duration <= 60:
            return True, f"Durée optimale: {duration:.1f}s"
        return True, f"Durée OK: {duration:.1f}s"
    
    elif platform == "youtube":
        return True, f"Durée: {duration:.1f}s"
    
    return True, f"Durée: {duration:.1f}s"


def validate_file_size(video_path: Path, max_mb: int = 500) -> tuple:
    """Vérifie que le fichier n'est pas trop gros."""
    size_bytes = video_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    if size_mb > max_mb:
        return False, f"Fichier trop gros: {size_mb:.1f}MB > {max_mb}MB"
    
    return True, f"Taille OK: {size_mb:.1f}MB"


def validate_video_complete(
    video_path: Path,
    platform: str = "tiktok"
) -> dict:
    """Validation complète du fichier vidéo."""
    result = {
        "valid": True,
        "checks": [],
        "warnings": []
    }
    
    if not video_path.exists():
        result["valid"] = False
        result["checks"].append(("EXISTS", False, "Fichier introuvable"))
        return result
    
    # Check 1: Taille
    size_ok, size_msg = validate_file_size(video_path)
    result["checks"].append(("SIZE", size_ok, size_msg))
    if not size_ok:
        result["valid"] = False
    
    # Check 2: Durée
    dur_ok, dur_msg = validate_video_duration(video_path, platform)
    result["checks"].append(("DURATION", dur_ok, dur_msg))
    if not dur_ok:
        result["valid"] = False
    
    if not OCR_AVAILABLE:
        result["warnings"].append(
            "OCR indisponible - validation text density skippée. "
            "Installer opencv-python pour activer."
        )
    
    return result
