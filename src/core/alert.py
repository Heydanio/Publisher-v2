import os
import requests

def send_discord_notification(message: str):
    """Envoie une alerte sur Discord via Webhook."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ Pas de Webhook Discord configuré.")
        return
    
    try:
        response = requests.post(webhook_url, json={"content": message})
        if response.status_code == 204:
            print("🔔 Notification Discord envoyée !")
    except Exception as e:
        print(f"❌ Erreur notification Discord : {e}")