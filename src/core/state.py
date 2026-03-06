import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Initialise la connexion à la base de données."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("❌ Erreur : SUPABASE_URL ou SUPABASE_KEY introuvable.")
        
    return create_client(url, key)

# --- NEW : Ajout de l'argument 'platform' ---
def is_video_published(account_name: str, drive_file_id: str, platform: str = "youtube") -> bool:
    """Vérifie si une vidéo a déjà été postée sur ce compte POUR cette plateforme."""
    supabase = get_supabase_client()
    # On filtre maintenant par compte, par fichier ET par plateforme
    response = supabase.table("published_videos").select("*") \
        .eq("account_name", account_name) \
        .eq("drive_file_id", drive_file_id) \
        .eq("platform", platform).execute() # <--- NEW
        
    return len(response.data) > 0

# --- NEW : Ajout de l'argument 'platform' ---
def mark_video_published(account_name: str, drive_file_id: str, platform: str = "youtube"):
    """Note dans la base de données que la vidéo a été publiée sur une plateforme donnée."""
    supabase = get_supabase_client()
    supabase.table("published_videos").insert({
        "account_name": account_name,
        "drive_file_id": drive_file_id,
        "platform": platform # <--- NEW
    }).execute()
    print(f"💾 État sauvegardé : La vidéo {drive_file_id} est marquée comme publiée sur {platform} pour {account_name}.")

# --- TEST LOCAL ---
if __name__ == "__main__":
    print("Tentative de connexion à Supabase...")
    # Test avec la nouvelle logique
    if not is_video_published("test_acc", "ID_TEST", platform="tiktok"):
        mark_video_published("test_acc", "ID_TEST", platform="tiktok")