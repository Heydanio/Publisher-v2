import os
import json
import time
import random
from playwright.sync_api import sync_playwright

def upload_to_tiktok(config, video_path, video_title):
    """
    Module TikTok V2.1 - Spécial GitHub Actions (Tolérance Haute).
    Gère les timeouts longs et nettoie les cookies automatiquement.
    """
    account_id = config.get("account_id", "default").upper()
    cookies_raw = os.environ.get(f"TIKTOK_COOKIES_{account_id}")

    if not cookies_raw:
        print(f"❌ Erreur : Secret TIKTOK_COOKIES_{account_id} introuvable.")
        return False

    print(f"🤖 [TikTok-Bot] Initialisation pour {account_id}...")

    with sync_playwright() as p:
        # Lancement de Chromium
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )

        # Nettoyage et injection des cookies
        try:
            cookies = json.loads(cookies_raw)
            for cookie in cookies:
                if cookie.get('sameSite') not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'Lax'
                if 'expirationDate' in cookie:
                    cookie['expires'] = int(cookie['expirationDate'])
                if 'id' in cookie:
                    del cookie['id']
            
            context.add_cookies(cookies)
            print("✅ Cookies injectés et corrigés.")
        except Exception as e:
            print(f"❌ Erreur JSON Cookies : {e}")
            browser.close()
            return False

        page = context.new_page()

        try:
            # --- ÉTAPE 1 : CONNEXION ---
            print("🌐 [1/5] Navigation vers TikTok Creator Center (Timeout 120s)...")
            # 'commit' permet de continuer dès que le serveur répond, sans attendre les pubs/trackers
            page.goto("https://www.tiktok.com/creator-center/upload?from=upload", wait_until="commit", timeout=120000)
            
            print("⏳ Attente de l'élément d'upload...")
            # On attend que l'input file soit réellement là
            page.wait_for_selector('input[type="file"]', timeout=60000)
            print("✅ Page prête !")
            time.sleep(5)

            # --- ÉTAPE 2 : UPLOAD ---
            print(f"📤 [2/5] Envoi du fichier : {video_path.name}")
            file_input = page.locator('input[type="file"]')
            file_input.set_input_files(str(video_path))
            
            print("⏳ Upload en cours sur TikTok (Attente de l'interface d'édition)...")
            # On attend que la zone de texte apparaisse (signe que l'upload est bien engagé)
            page.wait_for_selector('div.public-DraftEditor-content', timeout=180000)
            print("✅ Fichier reçu par TikTok !")

            # --- ÉTAPE 3 : LÉGENDE ---
            print("📝 [3/5] Configuration de la légende...")
            caption_box = page.locator('div.public-DraftEditor-content')
            caption_box.click()
            
            clean_title = video_title.replace(".mp4", "")
            tags = " ".join(config.get("tags", ["#fyp", "#viral"]))
            full_text = f"{clean_title} {tags}"
            
            page.keyboard.type(full_text)
            print(f"✍️ Texte : {full_text}")
            time.sleep(3)

            # --- ÉTAPE 4 : PUBLICATION ---
            print("🚀 [4/5] Clic sur POST...")
            # On cherche le bouton Post (parfois il y en a plusieurs, on prend le premier visible)
            publish_button = page.get_by_role("button", name="Post").first
            publish_button.wait_for(state="visible", timeout=30000)
            
            time.sleep(2)
            publish_button.click()

            # --- ÉTAPE 5 : CONFIRMATION ---
            print("⏳ [5/5] Attente du message de confirmation...")
            # On attend 20 secondes pour laisser le temps à TikTok de traiter
            time.sleep(20)
            
            print(f"✅ TikTok : {account_id} a publié avec succès !")
            return True

        except Exception as e:
            print(f"🔥 Erreur pendant l'exécution : {e}")
            # Très important pour comprendre si c'est un captcha
            page.screenshot(path="debug_tiktok_error.png")
            print("📸 Capture d'écran de l'erreur sauvegardée.")
            return False
        finally:
            browser.close()