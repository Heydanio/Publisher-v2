"""
Safeguards pour eviter les comportements detectables comme spam.
Validation du contenu avant upload.
"""
import re
from typing import List, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Tags spammy a eviter
SPAM_TAGS = {
    "follow4follow", "f4f", "like4like", "l4l", "follow", "followme",
    "spam", "sub4sub", "subforsub",
}

# Patterns de titres spammy
SPAM_PATTERNS = [
    r'\b(MUST WATCH|YOU WONT BELIEVE|GONE WRONG|GONE SEXUAL)\b',
    r'!{3,}',  # Plus de 3 points d'exclamation
    r'\?{3,}',  # Plus de 3 points d'interrogation
    r'[A-Z]{15,}',  # 15+ majuscules consecutives
]


def validate_tags(tags: List[str], platform: str = "youtube") -> Tuple[bool, str]:
    """
    Valide les tags pour eviter spam/shadowban.
    
    Args:
        tags: Liste de tags
        platform: youtube ou tiktok
    
    Returns:
        Tuple (valid: bool, reason: str)
    """
    if not tags:
        return False, "Aucun tag fourni"
    
    # Limite de nombre de tags
    max_tags = {"youtube": 15, "tiktok": 10}
    if len(tags) > max_tags.get(platform, 10):
        return False, f"Trop de tags: {len(tags)} > {max_tags[platform]}"
    
    # Verifier tags spammy
    spammy_found = []
    for tag in tags:
        clean_tag = tag.lower().replace("#", "").strip()
        if clean_tag in SPAM_TAGS:
            spammy_found.append(tag)
    
    if spammy_found:
        return False, f"Tags spammy detectes: {spammy_found}"
    
    # Verifier qu'il n'y a pas de doublons
    unique_tags = set(t.lower() for t in tags)
    if len(unique_tags) != len(tags):
        return False, "Tags dupliques detectes"
    
    return True, "OK"


def validate_title(title: str, platform: str = "youtube") -> Tuple[bool, str]:
    """
    Valide le titre pour eviter patterns spammy.
    
    Args:
        title: Titre a valider
        platform: youtube ou tiktok
    
    Returns:
        Tuple (valid: bool, reason: str)
    """
    if not title or len(title.strip()) < 3:
        return False, "Titre trop court"
    
    # Limites de longueur
    max_length = {"youtube": 100, "tiktok": 150}
    if len(title) > max_length.get(platform, 100):
        return False, f"Titre trop long: {len(title)} > {max_length[platform]}"
    
    # Verifier patterns spammy
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return False, f"Pattern spammy detecte: {pattern}"
    
    # Verifier ratio majuscules
    if len(title) > 10:
        upper_ratio = sum(1 for c in title if c.isupper()) / len(title)
        if upper_ratio > 0.7:
            return False, f"Trop de majuscules: {upper_ratio*100:.0f}%"
    
    return True, "OK"


def validate_description(description: str) -> Tuple[bool, str]:
    """Valide une description."""
    if not description:
        return True, "OK"  # Description vide OK
    
    if len(description) > 5000:
        return False, "Description trop longue (>5000 chars)"
    
    # Compter les hashtags
    hashtags = re.findall(r'#\w+', description)
    if len(hashtags) > 30:
        return False, f"Trop de hashtags: {len(hashtags)} > 30"
    
    return True, "OK"


def sanitize_content(text: str) -> str:
    """Nettoie le contenu de caracteres suspects."""
    # Supprimer caracteres invisibles/zero-width
    text = re.sub(r'[\u200B-\u200F\u2028-\u202F\uFEFF]', '', text)
    
    # Normaliser espaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
