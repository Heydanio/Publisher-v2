#!/usr/bin/env python3
"""Encode les secrets locaux en base64 pour GitHub Secrets"""

import base64
import json
from pathlib import Path

def encode_file(path: str) -> str:
    """Encode un fichier en base64"""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def main():
    print("🔐 Encoding des secrets locaux en base64...\n")
    
    secrets_dir = Path("secrets")
    if not secrets_dir.exists():
        print("❌ Dossier 'secrets/' non trouvé!")
        print("   Crée d'abord: mkdir secrets/")
        print("   Puis ajoute tes fichiers JSON dedans")
        return
    
    # Fichiers à encoder
    files = {
        "GDRIVE_SA_JSON_B64": "secrets/service_account.json",
        "YT_CLIENT_SECRETS_B64": "secrets/client_secrets.json",
        "YT_CREDENTIALS_B64": "secrets/credentials.json",
    }
    
    results = {}
    
    for secret_name, file_path in files.items():
        if Path(file_path).exists():
            try:
                b64 = encode_file(file_path)
                results[secret_name] = b64
                print(f"✅ {secret_name}")
                print(f"   Longueur: {len(b64)} caractères")
            except Exception as e:
                print(f"❌ {secret_name}: {e}")
        else:
            print(f"⏭️  {secret_name}: fichier non trouvé ({file_path})")
    
    print("\n" + "="*80)
    print("📋 AJOUTE CES SECRETS DANS GITHUB:")
    print("="*80)
    print("\nVa sur: https://github.com/heydanio/Publisher-v2")
    print("Settings → Secrets and variables → Actions → New repository secret\n")
    
    for secret_name, value in results.items():
        print(f"Name:  {secret_name}")
        print(f"Value: {value[:50]}...")
        print()
    
    print("⚠️  NE JAMAIS commiter ces valeurs!")
    print("✅ Les fichiers dans secrets/ restent locaux (dans .gitignore)")

if __name__ == "__main__":
    main()
