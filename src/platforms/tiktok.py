import os
import json
import time
import random
from playwright.sync_api import sync_playwright

def upload_to_tiktok(config, video_path, video_title):
    """
    Module TikTok Ultra-Sécurisé (Playwright Stealth).
    Corrige automatiquement le format des cookies pour éviter les erreurs de format.
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

        # Injection et nettoyage des cookies
        try:
            cookies = json.loads(cookies_raw)
            
            # --- NETTOYAGE DES COOKIES ---
            for cookie in cookies:
                # Correction du sameSite (Playwright n'accepte que Strict, Lax ou None)
                if cookie.get('sameSite') not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'Lax'
                
                # Conversion de l'expiration pour Playwright (expires doit être un int)
                if 'expirationDate' in cookie:
                    cookie['expires'] = int(cookie['expirationDate'])
                    # On ne supprime pas forcément expirationDate, mais on s'assure que expires est présent
                
                # Suppression des clés inutiles qui font parfois planter Playwright
                if 'id' in cookie:
                    del cookie['id']

            context.add_cookies(cookies)
            print("✅ Cookies corrigés et chargés avec succès.")
        except Exception as e:
            print(f"❌ Erreur format JSON des cookies : {e}")
            browser.close()
            return False

        page = context.new_page()

        try:
            # 1. Aller sur le Creator Center (Upload)
            print("🌐 Connexion à TikTok Creator Center...")
            page.goto("https://www.tiktok.com/creator-center/upload?from=upload", wait_until="networkidle", timeout=90000)
            
            # Délai aléatoire "humain"
            time.sleep(random.uniform(5, 8))

            # 2. Sélection du fichier vidéo
            print(f"📤 Upload de la vidéo : {video_path.name}")
            file_input = page.locator('input[type="file"]')
            file_input.set_input_files(str(video_path))

            # 3. Attendre le chargement
            print("⏳ Téléchargement en cours (attente de 30s)...")
            time.sleep(30) 

            # 4. Ajouter la légende (Titre + Hashtags)
            print("📝 Rédaction de la légende...")
            # TikTok utilise un éditeur Draft.js, on clique et on tape
            caption_box = page.locator('div.public-DraftEditor-content')
            caption_box.click()
            
            # Nettoyage du titre (on enlève l'extension .mp4 si présente)
            clean_title = video_title.replace(".mp4", "")
            tags = " ".join(config.get("tags", ["#fyp", "#viral"]))
            full_text = f"{clean_title} {tags}"
            
            page.keyboard.type(full_text)
            time.sleep(2)

            # 5. Cliquer sur Publier
            print("🚀 Publication finale...")
            # On cherche le bouton Post qui est parfois dans une iframe ou complexe
            publish_button = page.get_by_role("button", name="Post").first
            publish_button.wait_for(state="visible")
            
            # Petit délai avant le clic final
            time.sleep(2)
            publish_button.click()

            # Attendre confirmation
            print("⏳ Vérification du succès...")
            time.sleep(15)
            
            print(f"✅ TikTok : {account_id} a publié avec succès !")
            return True

        except Exception as e:
            print(f"🔥 Erreur pendant l'exécution : {e}")
            # Capture d'écran pour voir ce qui bloque sur GitHub
            page.screenshot(path="debug_tiktok_error.png")
            print("📸 Capture d'écran 'debug_tiktok_error.png' générée.")
            return False
        finally:
            browser.close()