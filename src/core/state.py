import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Initialise la connexion à la base de données."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("❌ Erreur : SUPABASE_URL ou SUPABASE_KEY introuvable dans l'environnement.")
        
    return create_client(url, key)

def is_video_published(account_name: str, drive_file_id: str) -> bool:
    """Vérifie si une vidéo a déjà été postée sur ce compte."""
    supabase = get_supabase_client()
    response = supabase.table("published_videos").select("*") \
        .eq("account_name", account_name) \
        .eq("drive_file_id", drive_file_id).execute()
        
    return len(response.data) > 0

def mark_video_published(account_name: str, drive_file_id: str):
    """Note dans la base de données que la vidéo a été publiée."""
    supabase = get_supabase_client()
    supabase.table("published_videos").insert({
        "account_name": account_name,
        "drive_file_id": drive_file_id
    }).execute()
    print(f"💾 État sauvegardé : La vidéo {drive_file_id} est marquée comme publiée pour {account_name}.")

# --- TEST LOCAL ---
if __name__ == "__main__":
    print("Tentative de connexion à Supabase...")
    
    if not is_video_published("youtube_compte1", "ID_VIDEO_TEST_123"):
        print("✅ La vidéo n'a pas encore été postée. On l'ajoute !")
        mark_video_published("youtube_compte1", "ID_VIDEO_TEST_123")
    else:
        print("⚠️ La vidéo est déjà marquée comme postée dans la base de données !")