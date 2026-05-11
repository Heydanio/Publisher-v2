import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Initialise la connexion à la base de données."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("❌ Erreur : SUPABASE_URL ou SUPABASE_KEY introuvable.")

    return create_client(url, key)


def is_video_published(account_name: str, drive_file_id: str, platform: str = "youtube") -> bool:
    """
    Vérifie si une vidéo a été publiée.
    
    ⚠️ IMPORTANT: Ne PAS catch d'exception ici!
    Si Supabase est down, l'exception remonte et le pipeline s'arrête.
    C'est la seule garantie d'idempotence.
    """
    supabase = get_supabase_client()
    
    # SELECT id (pas SELECT *) pour économiser la bande passante Supabase
    response = supabase.table("published_videos").select("id") \
        .eq("account_name", str(account_name)) \
        .eq("drive_file_id", str(drive_file_id)) \
        .eq("platform", str(platform)) \
        .limit(1) \
        .execute()

    return len(response.data) > 0


def mark_video_published(account_name: str, drive_file_id: str, platform: str = "youtube"):
    """Note dans la base de données que la vidéo a été publiée."""
    supabase = get_supabase_client()
    supabase.table("published_videos").insert({
        "account_name": account_name,
        "drive_file_id": drive_file_id,
        "platform": platform
    }).execute()
    print(f"💾 État sauvegardé : Vidéo {drive_file_id} publiée sur {platform} pour {account_name}.")


if __name__ == "__main__":
    print("🧪 Test de connexion Supabase...")
    try:
        if not is_video_published("test_acc", "ID_TEST", platform="tiktok"):
            mark_video_published("test_acc", "ID_TEST", platform="tiktok")
            print("✅ Test réussi!")
    except Exception as e:
        print(f"⚠️ Erreur (attendue en local sans secrets): {e}")
