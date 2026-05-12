"""
IP Quality Check 2026

YouTube et TikTok détectent les IPs datacenter (AWS, GCP, Azure, DO, etc.)
et les pénalisent fortement. GitHub Actions utilise des IPs Azure.

Ce module:
- Détecte si on est sur une IP datacenter
- Log un warning si oui
- Permet de désactiver l'upload si IP de mauvaise qualité (option)
"""
import os
import urllib.request
import json
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# IP ranges connus comme datacenter (échantillon - liste réelle bien plus longue)
DATACENTER_INDICATORS = {
    "amazon", "aws", "amazonaws",
    "google", "googlecloud", "gcp",
    "microsoft", "azure",
    "digitalocean", "linode", "vultr",
    "hetzner", "ovh", "scaleway",
    "github", "actions",
}


def get_public_ip() -> Optional[str]:
    """Récupère l'IP publique."""
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as r:
            data = json.loads(r.read().decode())
            return data.get("ip")
    except Exception as e:
        logger.warning(f"Impossible de récupérer l'IP: {e}")
        return None


def get_ip_info(ip: str) -> Optional[dict]:
    """Récupère info sur l'IP (org, ASN, country)."""
    try:
        with urllib.request.urlopen(f"http://ip-api.com/json/{ip}", timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        logger.warning(f"Impossible de récupérer info IP: {e}")
        return None


def is_datacenter_ip(ip_info: dict) -> tuple:
    """
    Détermine si l'IP est un datacenter.
    
    Returns:
        (is_datacenter: bool, reason: str)
    """
    if not ip_info:
        return False, "Pas d'info IP"
    
    # Check ISP/Org
    isp = (ip_info.get("isp", "") + " " + ip_info.get("org", "")).lower()
    
    for indicator in DATACENTER_INDICATORS:
        if indicator in isp:
            return True, f"Datacenter détecté: {indicator} dans '{isp}'"
    
    # Check si "hosting" mentionné
    if "hosting" in isp or "cloud" in isp or "server" in isp:
        return True, f"Hosting/Cloud détecté: '{isp}'"
    
    return False, f"IP résidentielle apparente: '{isp}'"


def check_ip_quality_now(strict: bool = False) -> dict:
    """
    Check complet de la qualité d'IP actuelle.
    
    Args:
        strict: Si True, raise exception sur datacenter
    
    Returns:
        dict avec status, ip, is_datacenter, warning
    """
    result = {
        "status": "unknown",
        "ip": None,
        "is_datacenter": None,
        "isp": None,
        "country": None,
        "warning": None,
    }
    
    ip = get_public_ip()
    if not ip:
        result["status"] = "error"
        result["warning"] = "Impossible de récupérer l'IP"
        return result
    
    result["ip"] = ip
    
    info = get_ip_info(ip)
    if info:
        result["isp"] = info.get("isp", "")
        result["country"] = info.get("country", "")
        
        is_dc, reason = is_datacenter_ip(info)
        result["is_datacenter"] = is_dc
        
        if is_dc:
            result["status"] = "warning"
            result["warning"] = (
                f"⚠️ IP datacenter détectée! {reason}. "
                f"Risque de shadowban élevé en 2026."
            )
            logger.warning(result["warning"])
            
            if strict:
                raise RuntimeError("Datacenter IP refusée (strict mode)")
        else:
            result["status"] = "ok"
            logger.info(f"✅ IP OK: {ip} ({info.get('isp', 'unknown')})")
    
    return result
