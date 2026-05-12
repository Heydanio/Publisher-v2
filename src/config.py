"""Configuration centralisee avec validation."""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScheduleConfig:
    slots_hours: List[int] = field(default_factory=list)

    def is_publishing_time(self, current_hour: int, current_minute: int) -> bool:
        return current_hour in self.slots_hours and current_minute < 55


@dataclass
class ContentConfig:
    descriptions_file: Optional[str] = None
    tags_pool: List[str] = field(default_factory=list)
    youtube_category: str = "Entertainment"


@dataclass
class RateLimitConfig:
    max_per_day: Optional[int] = None
    min_gap_minutes: Optional[int] = None
    max_per_hour: Optional[int] = None


@dataclass
class AccountConfig:
    platform: str
    account_id: str
    account_name: str
    drive_folder_ids: List[str] = field(default_factory=list)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    content: ContentConfig = field(default_factory=ContentConfig)
    tags: List[str] = field(default_factory=lambda: ["#fyp", "#viral"])
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    def __post_init__(self) -> None:
        if self.platform not in ("youtube", "tiktok"):
            raise ValueError(f"Platform invalide: '{self.platform}'")
        if not self.account_id:
            raise ValueError("account_id ne peut pas etre vide")
        if not self.drive_folder_ids:
            env_id = os.environ.get("DRIVE_FOLDER_ID")
            if env_id:
                self.drive_folder_ids = [env_id]
            else:
                raise ValueError("drive_folder_ids vide et DRIVE_FOLDER_ID env non defini")

    def get_rate_limits(self) -> Dict[str, int]:
        from src.core.rate_limiter import DEFAULT_LIMITS
        defaults = DEFAULT_LIMITS.get(self.platform, DEFAULT_LIMITS["youtube"])
        
        return {
            "max_per_day": self.rate_limit.max_per_day or defaults["max_per_day"],
            "min_gap_minutes": self.rate_limit.min_gap_minutes or defaults["min_gap_minutes"],
            "max_per_hour": self.rate_limit.max_per_hour or defaults["max_per_hour"],
        }


def load_account_config(account_name: str) -> AccountConfig:
    """Charge une config depuis fichier JSON."""
    config_path = Path(f"config/{account_name}.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Config introuvable: {config_path}")

    logger.info(f"Chargement: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # Substituer les placeholders $DRIVE_FOLDER_ID* par les variables d'env
    drive_folder_ids = []
    for folder_id in data.get("drive_folder_ids", []):
        if folder_id.startswith("$"):
            # C'est un placeholder (ex: $DRIVE_FOLDER_ID ou $DRIVE_FOLDER_ID_2)
            env_var = folder_id[1:]  # enlever le $
            resolved = os.environ.get(env_var, folder_id)
            drive_folder_ids.append(resolved)
        else:
            # C'est un vrai folder ID
            drive_folder_ids.append(folder_id)
    
    if not drive_folder_ids:
        env_id = os.environ.get("DRIVE_FOLDER_ID", "")
        if env_id:
            drive_folder_ids = [env_id]

    schedule = ScheduleConfig(slots_hours=data.get("schedule", {}).get("slots_hours", []))
    
    content_data = data.get("content", {})
    content = ContentConfig(
        descriptions_file=content_data.get("descriptions_file"),
        tags_pool=content_data.get("tags_pool", []),
        youtube_category=content_data.get("youtube_category", "Entertainment")
    )
    
    rate_limit_data = data.get("rate_limit", {})
    rate_limit = RateLimitConfig(
        max_per_day=rate_limit_data.get("max_per_day"),
        min_gap_minutes=rate_limit_data.get("min_gap_minutes"),
        max_per_hour=rate_limit_data.get("max_per_hour"),
    )

    return AccountConfig(
        platform=data["platform"],
        account_id=data["account_id"],
        account_name=account_name,
        drive_folder_ids=drive_folder_ids,
        schedule=schedule,
        content=content,
        tags=data.get("tags", ["#fyp", "#viral"]),
        rate_limit=rate_limit,
    )


def get_required_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Variable d'environnement requise: {key}")
    return value
