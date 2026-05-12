"""
Timing humain 2026 (avec jitter anti-cron-pattern).

Évite les patterns parfaits style "toujours 18:00:00" qui sont
détectés comme bots par les algos 2026.
"""
import random
import time
from datetime import datetime, timedelta
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


def human_delay(base_seconds: int = 60, variance: float = 0.5) -> None:
    """
    Délai humain avec distribution gaussienne.
    
    Args:
        base_seconds: Durée moyenne
        variance: Variance (0.5 = ±50%)
    """
    # Distribution gaussienne pour comportement humain
    sigma = base_seconds * variance / 2
    delay = max(5, int(random.gauss(base_seconds, sigma)))
    
    minutes = delay // 60
    logger.info(f"Delai humain: {delay}s ({minutes}min)")
    time.sleep(delay)


def get_jittered_upload_time(
    scheduled_hour: int, 
    platform: str = "tiktok"
) -> datetime:
    """
    Retourne datetime cible pour l'upload avec jitter.
    
    Au lieu de 18:00:00 exactement, on aura par exemple 18:07:32.
    Distribution gaussienne centrée sur l'heure planifiée.
    
    Args:
        scheduled_hour: Heure planifiée (ex: 18)
        platform: "tiktok" ou "youtube"
    """
    if platform == "tiktok":
        # σ=7min, cap ±14min (validé par recherche 2026)
        jitter_minutes = int(random.gauss(0, 7))
        jitter_minutes = max(-14, min(14, jitter_minutes))
    else:  # youtube
        # σ=10min, cap ±20min
        jitter_minutes = int(random.gauss(0, 10))
        jitter_minutes = max(-20, min(20, jitter_minutes))
    
    jitter_seconds = random.randint(0, 59)
    
    now = datetime.now()
    target = now.replace(hour=scheduled_hour, minute=0, second=0, microsecond=0)
    target += timedelta(minutes=jitter_minutes, seconds=jitter_seconds)
    
    return target


def wait_until_jittered_time(scheduled_hour: int, platform: str = "tiktok") -> None:
    """
    Attend jusqu'à l'heure cible avec jitter.
    
    Si l'heure est dépassée, n'attend pas (upload immédiat).
    """
    target = get_jittered_upload_time(scheduled_hour, platform)
    now = datetime.now()
    
    if target > now:
        delta = (target - now).total_seconds()
        logger.info(f"Attente jusqu'à {target.strftime('%H:%M:%S')} ({int(delta)}s)")
        time.sleep(delta)
    else:
        logger.info(f"Heure cible déjà passée ({target.strftime('%H:%M:%S')})")


def is_in_publishing_window(
    scheduled_hours: list,
    current_dt: Optional[datetime] = None,
    tolerance_minutes: int = 25
) -> bool:
    """
    Vérifie si on est dans une fenêtre acceptable autour d'une heure planifiée.
    
    Tolerance ±25min permet de gérer les délais GitHub Actions.
    """
    if current_dt is None:
        current_dt = datetime.now()
    
    for hour in scheduled_hours:
        scheduled = current_dt.replace(hour=hour, minute=0, second=0)
        diff_minutes = abs((current_dt - scheduled).total_seconds() / 60)
        if diff_minutes <= tolerance_minutes:
            return True
    
    return False
