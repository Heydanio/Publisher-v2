"""
Anti-Shadowban Engine 2026 (TITAN COLOSSAL V3)

Module central regroupant toutes les protections anti-detection
basées sur le rapport d'expertise 2026:
- Hashtag blacklist (TikTok)
- Keyword variations detection (misspelled bypass)
- Frequency caps platform-specific
- Timing jitter (anti-cron-pattern)
- Format randomization (anti-repetition)
- Information gain validation
"""
import re
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# HASHTAGS & KEYWORDS BLACKLIST (TikTok 2026)
# ============================================================================

TIKTOK_BANNED_HASHTAGS_2026 = {
    # === SUBSTANCES (bannissement total) ===
    "#marijuana", "#cannabis", "#weed", "#420",
    "#fentanyl", "#heroin", "#cocaine", "#meth",
    "#oxycodone", "#methamphetamine", "#whippet",
    "#mdma", "#lsd", "#shrooms", "#crack",
    
    # === CONTENU ADULTE & CODE WORDS ===
    "#seggs", "#corn", "#onlyfans", "#oflinkinbio",
    "#sxworker", "#s*xworker", "#accountant",
    "#nsfw", "#kinky", "#feet",
    
    # === FINANCE HAUT RISQUE ===
    "#stocksignals", "#pumpanddump", "#cryptogains",
    "#amazonfba", "#linkinbio", "#getrichquick",
    "#daytrader", "#binaryoptions", "#forexsignals",
    
    # === SPAM PATTERNS (réduit la portée) ===
    "#fyp", "#foryou", "#foryoupage", "#viral",
    "#trending", "#followforfollow", "#likeforlike",
    "#f4f", "#l4l", "#followtrain", "#like4like",
    "#followback", "#viralvideo", "#trend",
    
    # === SENSIBLE / HEALTH ===
    "#loseweight", "#weightloss", "#diet",
    "#unalive", "#sewerslide",  # code suicide
    "#thinspo", "#proana",  # eating disorders
    
    # === MISLEADING ===
    "#youwontbelieve", "#shocking", "#doctorshate",
}

BANNED_KEYWORDS_2026 = {
    # Drogues (exact + tentatives évitement)
    "fentanyl", "heroin", "cocaine", "oxycodone",
    "marijuana", "cannabis", "methamphetamine",
    
    # OnlyFans code words
    "accountant", "spicy accountant",
    
    # Self-harm code
    "unalive", "sewerslide", "kms",
    
    # Adult code
    "seggs", "corn 🌽",
}

# Patterns de substitution courants (TikTok OCR détecte!)
LEETSPEAK_PATTERNS = {
    'a': ['@', '4'],
    'e': ['3'],
    'i': ['1', '!'],
    'o': ['0'],
    's': ['$', '5'],
    'l': ['1'],
    'g': ['9'],
}


def normalize_leetspeak(text: str) -> str:
    """Normalise le leetspeak pour détecter les variations bannies."""
    normalized = text.lower()
    reverse_map = {}
    for letter, substitutes in LEETSPEAK_PATTERNS.items():
        for sub in substitutes:
            reverse_map[sub] = letter
    
    for sub, letter in reverse_map.items():
        normalized = normalized.replace(sub, letter)
    
    return normalized


def validate_hashtags(tags: list, platform: str = "tiktok") -> tuple:
    """
    Vérifie les hashtags contre la blacklist 2026.
    
    Returns:
        (is_valid: bool, message: str)
    """
    if platform != "tiktok":
        return True, "Platform non-tiktok, skip"
    
    violations = []
    for tag in tags:
        tag_lower = tag.lower().strip()
        if not tag_lower.startswith("#"):
            tag_lower = "#" + tag_lower
        
        # Check exact
        if tag_lower in TIKTOK_BANNED_HASHTAGS_2026:
            violations.append(f"BANNI: {tag}")
        
        # Check leetspeak normalization
        normalized = "#" + normalize_leetspeak(tag_lower.lstrip("#"))
        if normalized in TIKTOK_BANNED_HASHTAGS_2026:
            violations.append(f"VARIATION BANNIE: {tag} → {normalized}")
    
    if violations:
        return False, " | ".join(violations)
    return True, "Hashtags OK"


def validate_keywords_in_text(text: str) -> tuple:
    """
    Détecte les mots-clés bannies (exact + variations leetspeak).
    
    Returns:
        (is_valid: bool, violations: list)
    """
    violations = []
    text_lower = text.lower()
    normalized = normalize_leetspeak(text_lower)
    
    for keyword in BANNED_KEYWORDS_2026:
        if keyword in text_lower:
            violations.append(f"EXACT: {keyword}")
        elif keyword in normalized:
            violations.append(f"LEET: {keyword}")
    
    return len(violations) == 0, violations


# ============================================================================
# FREQUENCY CAPS (Platform-Specific 2026)
# ============================================================================

FREQUENCY_RULES_2026 = {
    "tiktok": {
        "max_per_day": 2,           # 2026: max 2/jour sain
        "max_per_week": 5,          # Optimal: 3-5/semaine
        "min_gap_minutes": 180,     # 3h minimum entre uploads
        "max_per_hour": 1,
        "warming_uploads_max_per_day": 1,  # Pendant warming
    },
    "youtube": {
        "max_per_day": 3,
        "max_per_week": 7,          # 3-5 shorts + 1-2 long
        "min_gap_minutes": 120,
        "max_per_hour": 1,
        "warming_uploads_max_per_day": 1,
    }
}


def get_frequency_rules(platform: str) -> dict:
    """Retourne les règles de fréquence pour la plateforme."""
    return FREQUENCY_RULES_2026.get(platform, FREQUENCY_RULES_2026["tiktok"])


# ============================================================================
# TIMING JITTER (Anti-Cron-Pattern)
# ============================================================================

def get_jittered_time(base_hour: int, platform: str = "tiktok") -> tuple:
    """
    Retourne (hour, minute, second) avec jitter aléatoire.
    
    Évite les patterns parfaits genre 18:00:00 qui sont détectés.
    Distribution gaussienne pour un comportement plus humain.
    """
    if platform == "tiktok":
        jitter_minutes = int(random.gauss(0, 7))  # σ=7min
        jitter_minutes = max(-14, min(14, jitter_minutes))  # cap ±14
    else:  # youtube
        jitter_minutes = int(random.gauss(0, 10))  # σ=10min
        jitter_minutes = max(-20, min(20, jitter_minutes))  # cap ±20
    
    jitter_seconds = random.randint(0, 59)
    
    base = datetime.now().replace(
        hour=base_hour, 
        minute=0, 
        second=0, 
        microsecond=0
    )
    actual = base + timedelta(minutes=jitter_minutes, seconds=jitter_seconds)
    return actual.hour, actual.minute, actual.second


def is_publishing_window(scheduled_hours: list, current_dt: datetime, 
                         tolerance_minutes: int = 25) -> bool:
    """
    Vérifie si on est dans une fenêtre de publication acceptable.
    
    Tolérance ±25 min autour de l'heure planifiée.
    """
    for hour in scheduled_hours:
        scheduled = current_dt.replace(hour=hour, minute=0, second=0)
        diff_minutes = abs((current_dt - scheduled).total_seconds() / 60)
        if diff_minutes <= tolerance_minutes:
            return True
    return False


# ============================================================================
# FORMAT RANDOMIZATION (Anti format répétitif)
# ============================================================================

DESCRIPTION_TEMPLATES_2026 = [
    "{title}\n\n{tags}",
    "{title} 🔥\n\n{tags}",
    "{title}\n\n👉 {tags}",
    "{title} ✨\n\n#shorts {tags}",
    "{title}\n\n{tags}\n\nDon't forget to follow!",
    "{title}\n\n💫 {tags}",
    "{title} 🎬\n\n{tags}",
    "{title}\n\n→ {tags}",
]

EMOJI_VARIATIONS = [
    "🔥", "✨", "💫", "🎬", "🎯", "💥", "⚡", "🌟",
    "🎉", "🚀", "💪", "👀", "🎵", "💜", "🌈", "⭐"
]


def generate_varied_description(
    title: str, 
    tags: list, 
    seed: Optional[str] = None
) -> str:
    """
    Génère une description avec variation aléatoire.
    
    Évite le pattern "même structure à chaque post" qui flag les bots.
    
    Args:
        title: Titre de la vidéo
        tags: Liste de hashtags
        seed: Seed optionnel pour reproductibilité (ex: video_id)
    """
    if seed:
        # Déterministe par vidéo mais varié globalement
        random.seed(hashlib.md5(seed.encode()).hexdigest())
    
    template = random.choice(DESCRIPTION_TEMPLATES_2026)
    tags_str = " ".join(tags[:5])  # Max 5 hashtags
    
    description = template.format(title=title, tags=tags_str)
    
    # Reset seed
    if seed:
        random.seed()
    
    return description


def randomize_tag_order(tags: list, seed: Optional[str] = None) -> list:
    """Randomise l'ordre des tags (anti-pattern)."""
    if seed:
        random.seed(hashlib.md5(seed.encode()).hexdigest())
    
    tags_copy = tags.copy()
    random.shuffle(tags_copy)
    
    if seed:
        random.seed()
    
    return tags_copy


# ============================================================================
# INFORMATION GAIN CHECK (Anti contenu dupliqué - YouTube 2026)
# ============================================================================

def calculate_content_fingerprint(title: str, description: str = "") -> str:
    """
    Calcule une empreinte sémantique simplifiée du contenu.
    
    YouTube 2026 détecte les contenus trop similaires via LLM,
    mais on peut au moins éviter les titres trop répétitifs.
    """
    combined = f"{title.lower()} {description.lower()}"
    # Normalize whitespace, remove emoji, etc.
    cleaned = re.sub(r'[^\w\s]', '', combined)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return hashlib.md5(cleaned.encode()).hexdigest()


def check_information_gain(
    title: str,
    description: str,
    recent_titles: list,
    similarity_threshold: float = 0.7
) -> tuple:
    """
    Vérifie que le contenu apporte du nouveau.
    
    Comparaison naïve par mots communs.
    En production: utiliser embeddings (sentence-transformers).
    """
    title_words = set(re.findall(r'\w+', title.lower()))
    
    for recent in recent_titles:
        recent_words = set(re.findall(r'\w+', recent.lower()))
        if not title_words or not recent_words:
            continue
        
        intersection = title_words & recent_words
        union = title_words | recent_words
        jaccard = len(intersection) / len(union) if union else 0
        
        if jaccard > similarity_threshold:
            return False, f"Trop similaire à: '{recent}' ({jaccard:.0%})"
    
    return True, "Originalité OK"


# ============================================================================
# MASTER VALIDATION FUNCTION
# ============================================================================

def validate_upload_2026(
    platform: str,
    title: str,
    tags: list,
    description: str = "",
    recent_titles: Optional[list] = None
) -> dict:
    """
    Validation complète pre-upload 2026.
    
    Returns:
        dict avec:
            - valid: bool
            - score: 0-100 (risque)
            - errors: list (bloquants)
            - warnings: list (non-bloquants)
            - suggestions: list
    """
    result = {
        "valid": True,
        "score": 100,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Check 1: Hashtags blacklist
    ht_ok, ht_msg = validate_hashtags(tags, platform)
    if not ht_ok:
        result["valid"] = False
        result["score"] -= 40
        result["errors"].append(f"🚫 {ht_msg}")
    
    # Check 2: Keywords in title/description
    text_combined = f"{title} {description}"
    kw_ok, kw_violations = validate_keywords_in_text(text_combined)
    if not kw_ok:
        result["valid"] = False
        result["score"] -= 50
        result["errors"].extend([f"🚫 Keyword banni: {v}" for v in kw_violations])
    
    # Check 3: Information Gain (originalité)
    if recent_titles:
        ig_ok, ig_msg = check_information_gain(title, description, recent_titles)
        if not ig_ok:
            result["score"] -= 20
            result["warnings"].append(f"⚠️ {ig_msg}")
            result["suggestions"].append("Varier davantage les titres")
    
    # Check 4: Title quality (capslock, etc.)
    if title:
        caps_ratio = sum(1 for c in title if c.isupper()) / max(len(title), 1)
        if caps_ratio > 0.7:
            result["score"] -= 15
            result["warnings"].append("⚠️ Titre majoritairement en MAJUSCULES")
        
        if title.count('!') > 3 or title.count('?') > 3:
            result["score"] -= 10
            result["warnings"].append("⚠️ Ponctuation excessive")
    
    # Check 5: Hashtag count
    if len(tags) > 5 and platform == "tiktok":
        result["score"] -= 5
        result["suggestions"].append("TikTok 2026: 3-5 hashtags optimaux")
    
    return result


def log_validation_result(result: dict, video_name: str) -> None:
    """Log structuré du résultat de validation."""
    logger.info(f"━━━ Validation 2026: {video_name[:60]} ━━━")
    logger.info(f"Score risque: {result['score']}/100")
    
    if result["errors"]:
        for err in result["errors"]:
            logger.error(err)
    
    if result["warnings"]:
        for warn in result["warnings"]:
            logger.warning(warn)
    
    if result["suggestions"]:
        for sug in result["suggestions"]:
            logger.info(f"💡 {sug}")
    
    if result["valid"]:
        logger.info("✅ Upload AUTORISÉ")
    else:
        logger.error("❌ Upload BLOQUÉ par les safeguards 2026")
