"""
Safeguards centralisés - Pipeline Anti-Shadowban 2026

Ce module orchestre toutes les validations:
- anti_shadowban (hashtags, keywords, frequency)
- content_validator (durée, taille, OCR)
- ip_quality (datacenter detection)
- warming (phase d'âge du compte)
"""
import re
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger
from src.core.anti_shadowban import (
    validate_hashtags as _validate_hashtags_new,
    validate_keywords_in_text,
    validate_upload_2026,
    log_validation_result,
    generate_varied_description,
    randomize_tag_order,
)

logger = get_logger(__name__)


# === Legacy compatibility ===

def validate_tags(tags: list, platform: str = "tiktok") -> tuple:
    """
    Validation legacy + nouvelle validation 2026.
    
    Returns:
        (valid: bool, reason: str)
    """
    return _validate_hashtags_new(tags, platform)


def sanitize_content(text: str) -> str:
    """
    Nettoie le contenu (zero-width chars, whitespace, etc.).
    """
    if not text:
        return ""
    
    # Remove zero-width characters
    zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2028', '\u2029']
    for char in zero_width_chars:
        text = text.replace(char, '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip
    return text.strip()


# === New 2026 validation ===

def run_full_validation(
    platform: str,
    title: str,
    tags: list,
    description: str = "",
    video_path: Optional[Path] = None,
    recent_titles: Optional[list] = None,
    log_result: bool = True
) -> dict:
    """
    Pipeline de validation complet 2026.
    
    Returns:
        dict avec validation complète
    """
    # Phase 1: Anti-shadowban (hashtags, keywords, IG)
    result = validate_upload_2026(
        platform=platform,
        title=title,
        tags=tags,
        description=description,
        recent_titles=recent_titles or []
    )
    
    # Phase 2: Content validator (optional, si vidéo dispo)
    if video_path and video_path.exists():
        try:
            from src.core.content_validator import validate_video_complete
            content_result = validate_video_complete(video_path, platform)
            
            for check_name, check_ok, check_msg in content_result.get("checks", []):
                if not check_ok:
                    result["valid"] = False
                    result["score"] -= 20
                    result["errors"].append(f"📹 {check_name}: {check_msg}")
            
            result["warnings"].extend(content_result.get("warnings", []))
        except ImportError:
            logger.debug("content_validator non disponible")
    
    if log_result:
        log_validation_result(result, title[:60])
    
    return result
