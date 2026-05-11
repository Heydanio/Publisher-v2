"""
Delais intelligents pour eviter la detection de patterns.
Utilise des distributions Gaussiennes et du jitter pour simuler du comportement humain.
"""
import random
import time
from datetime import datetime
from typing import List
from src.utils.logger import get_logger

logger = get_logger(__name__)


def human_delay(base_seconds: int = 300, variance: float = 0.3) -> int:
    """
    Delai aleatoire suivant une distribution gaussienne.
    
    Args:
        base_seconds: Delai moyen souhaite
        variance: Pourcentage de variation (0.3 = 30%)
    
    Returns:
        Delai applique en secondes
    """
    # Distribution gaussienne = comportement plus humain qu'uniforme
    actual = random.gauss(base_seconds, base_seconds * variance)
    
    # Bornes pour eviter valeurs extremes
    min_delay = max(60, int(base_seconds * 0.3))
    max_delay = int(base_seconds * 2)
    actual = max(min_delay, min(int(actual), max_delay))
    
    logger.info(f"Delai humain: {actual}s ({actual//60}min)")
    time.sleep(actual)
    return actual


def get_next_run_jitter(scheduled_hour: int) -> tuple:
    """
    Ajoute du jitter a une heure planifiee pour eviter patterns.
    
    Args:
        scheduled_hour: Heure planifiee (ex: 9 pour 9h00)
    
    Returns:
        Tuple (hour, minute) avec jitter applique
    """
    # Jitter de +/- 15 minutes autour de l'heure
    minute = random.randint(0, 29)
    return (scheduled_hour, minute)


def avoid_round_numbers(seconds: int) -> int:
    """
    Evite les nombres ronds qui sont suspects.
    
    Args:
        seconds: Duree en secondes
    
    Returns:
        Duree legerement modifiee
    """
    if seconds % 60 == 0:
        # Si pile sur la minute, ajoute 1-59 secondes
        return seconds + random.randint(7, 53)
    return seconds


def get_realistic_user_agent() -> str:
    """Retourne un User-Agent realiste et recent."""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    return random.choice(agents)
