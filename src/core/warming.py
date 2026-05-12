"""
Warming Period Tracker 2026

Stratégie 14 jours pour réchauffer un compte automatisé:
- Jours 1-3: Incubation (scroll uniquement)
- Jours 4-7: Engagement léger
- Jours 8-14: Montée en charge
- Jour 15+: Plein régime

Le 1er upload ne devrait JAMAIS être avant le jour 8.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


WARMING_PHASES = {
    "incubation": (1, 3),       # Jours 1-3: aucun upload
    "socialization": (4, 7),    # Jours 4-7: aucun upload, engage seulement
    "ramp_up": (8, 14),         # Jours 8-14: 1 upload/jour MAX
    "full_speed": (15, None),   # 15+: rythme normal
}


def get_account_age_days(account_created_at: Optional[datetime]) -> Optional[int]:
    """Calcule l'âge du compte en jours."""
    if not account_created_at:
        return None
    
    now = datetime.now(timezone.utc)
    if account_created_at.tzinfo is None:
        account_created_at = account_created_at.replace(tzinfo=timezone.utc)
    
    return (now - account_created_at).days


def get_warming_phase(age_days: Optional[int]) -> str:
    """Retourne la phase de warming actuelle."""
    if age_days is None:
        return "unknown"
    
    for phase, (start, end) in WARMING_PHASES.items():
        if end is None and age_days >= start:
            return phase
        elif end is not None and start <= age_days <= end:
            return phase
    
    return "unknown"


def check_warming_allows_upload(
    age_days: Optional[int],
    uploads_today: int = 0
) -> tuple:
    """
    Vérifie si la phase de warming autorise un upload.
    
    Returns:
        (allowed: bool, reason: str, phase: str)
    """
    if age_days is None:
        # Si on ne connaît pas l'âge, on permet (legacy accounts)
        return True, "Âge inconnu, upload autorisé", "unknown"
    
    phase = get_warming_phase(age_days)
    
    if phase == "incubation":
        return False, f"Jour {age_days}/14 - INCUBATION (aucun upload)", phase
    
    if phase == "socialization":
        return False, f"Jour {age_days}/14 - SOCIALISATION (engage seulement)", phase
    
    if phase == "ramp_up":
        if uploads_today >= 1:
            return False, f"Jour {age_days}/14 - RAMP UP (max 1 upload/jour)", phase
        return True, f"Jour {age_days}/14 - RAMP UP (1 upload autorisé)", phase
    
    if phase == "full_speed":
        return True, f"Jour {age_days} - FULL SPEED", phase
    
    return True, f"Phase inconnue: {phase}", phase


def get_warming_recommendations(phase: str) -> list:
    """Retourne des recommandations selon la phase."""
    recommendations = {
        "incubation": [
            "🚫 Aucun upload pendant 3 jours",
            "👀 Scroll passif la FYP/feed seulement",
            "⏱️ 5-10min/jour minimum",
            "🎯 Voir des vidéos de ta niche entières"
        ],
        "socialization": [
            "🚫 Toujours pas d'upload",
            "❤️ 5-10 likes/jour (vidéos de la niche)",
            "💬 2-3 commentaires authentiques",
            "👤 Follow 3-5 créateurs clés"
        ],
        "ramp_up": [
            "📤 1 upload/jour MAX",
            "🎯 Contenu de très haute qualité",
            "❤️ Continue l'engagement actif",
            "📊 Monitor stats quotidiennement"
        ],
        "full_speed": [
            "📤 Rythme normal autorisé (3-5/sem TikTok)",
            "📈 Optimise content basé sur analytics",
            "🔄 Continue diversification format"
        ]
    }
    
    return recommendations.get(phase, ["Phase non reconnue"])
