import os
import json
import time
import random
from playwright.sync_api import sync_playwright

def upload_to_tiktok(config, video_path, video_title):
    """
    Module TikTok Ultra-Sécurisé (Playwright Stealth).
    Simule une navigation humaine pour éviter le shadowban.
    """
    account_id = config.get("account_id", "default").upper()
    # On récupère les cookies JSON depuis le secret GitHub
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    print(f"🤖 [TikTok-Bot] Initialisation de l'upload pour {account_id}...")

    with sync_playwright() as p:
        # Lancement du navigateur (headless=True pour GitHub Actions)
        browser = p.chromium.launch(headless=True)
        
        # On définit un User-Agent moderne et une résolution standard
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )

        # Injection massive des cookies
        try:
            cookies = json.loads(cookies_raw)
            context.add_cookies(cookies)
        except Exception as e:
            print(f"❌ Erreur format JSON des cookies : {e}")
            return False

        page = context.new_page()

        try:
            # 1. Aller sur le Creator Center (Upload)
            print("🌐 Connexion à TikTok Creator Center...")
            page.goto("https://www.tiktok.com/creator-center/upload?from=upload", wait_until="domcontentloaded", timeout=60000)
            
            # Petit délai aléatoire pour faire "humain"
            time.sleep(random.uniform(3, 5))

            # 2. Sélection du fichier vidéo
            print(f"📤 Upload de la vidéo : {video_path}")
            # On cible l'input file caché de TikTok
            file_input = page.locator('input[type="file"]')
            file_input.set_input_files(video_path)

            # 3. Attendre que l'upload soit fini (TikTok affiche souvent un aperçu ou un texte "Edit")
            print("⏳ Téléchargement en cours (attente de 20s minimum)...")
            time.sleep(20) # Sécurité pour laisser le fichier monter

            # 4. Ajouter la légende (Titre + Hashtags)
            print("📝 Rédaction de la légende...")
            # On cherche la zone de texte éditable
            caption_box = page.locator('div.public-DraftEditor-content')
            caption_box.click()
            
            # On combine le titre GDrive + tes tags du JSON
            tags = " ".join(config.get("tags", ["#fyp", "#viral"]))
            full_text = f"{video_title} {tags}"
            
            page.keyboard.type(full_text)
            time.sleep(2)

            # 5. Cliquer sur Publier (Post)
            print("🚀 Publication finale...")
            # On cherche le bouton qui contient "Post" ou "Publier"
            publish_button = page.get_by_role("button", name="Post")
            publish_button.wait_for(state="visible")
            publish_button.click()

            # Attendre la confirmation (petit message de succès)
            time.sleep(10)
            print(f"✅ TikTok : {account_id} a publié avec succès !")
            return True

        except Exception as e:
            print(f"🔥 Erreur pendant l'exécution : {e}")
            # En cas d'erreur, on prend une capture d'écran pour le debug GitHub Actions
            page.screenshot(path="debug_tiktok_error.png")
            return False
        finally:
            browser.close()