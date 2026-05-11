#!/bin/bash
# Script pour configurer les credentials EN LOCAL (jamais committé)

echo "⚠️  Ce script configure tes credentials LOCALEMENT"
echo "   Les fichiers créés ne seront JAMAIS committé (ils sont dans .gitignore)"
echo ""

# Crée le dossier secrets/ local
mkdir -p secrets/

# Instructions
echo "Ajoute tes fichiers JSON dans le dossier secrets/:"
echo "  - secrets/client_secrets.json"
echo "  - secrets/credentials.json"
echo "  - secrets/service_account.json"
echo ""
echo "Puis exécute: python3 encode_secrets.py"
echo ""
echo "Les valeurs en base64 iront dans GitHub Secrets"
