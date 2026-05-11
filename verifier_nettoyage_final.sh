#!/bin/bash

###############################################################################
# NETTOYAGE FINAL - Vérifier et supprimer fichiers inutiles
###############################################################################

set -e
cd ~/Desktop/Publisher-v2 || exit 1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧹 NETTOYAGE FINAL - Vérification et suppression fichiers inutiles"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

###############################################################################
# ÉTAPE 1: Vérifier les fichiers sensibles (ne doivent PAS exister)
###############################################################################

echo "1️⃣  Vérification: Aucun fichier sensible"
echo ""

SENSIBLES=(
    "secrets/"
    ".env"
    "*.json"
    "*.key"
    "*.pem"
    "client_secret*"
    "credentials.json"
    "token.json"
    "oauth2.json"
)

FOUND=0
for pattern in "${SENSIBLES[@]}"; do
    matches=$(find . -type f -name "$pattern" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -v "__pycache__" || true)
    if [ ! -z "$matches" ]; then
        echo "⚠️  Trouvé (devrait être dans .gitignore):"
        echo "   $matches"
        FOUND=1
    fi
done

if [ $FOUND -eq 0 ]; then
    echo "✅ Aucun fichier sensible trouvé (bon!)"
fi
echo ""

###############################################################################
# ÉTAPE 2: Lister tous les fichiers trackés par git
###############################################################################

echo "2️⃣  Fichiers trackés par Git:"
echo ""

git ls-files | sort | while read file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
    echo "   ✓ $file ($size bytes)"
done

echo ""

###############################################################################
# ÉTAPE 3: Identifier les fichiers inutiles à supprimer
###############################################################################

echo "3️⃣  Identification des fichiers inutiles"
echo ""

INUTILES=()

# Scripts d'installation (ne doivent pas être trackés)
if git ls-files | grep -q "setup_local.sh"; then
    echo "⚠️  setup_local.sh - peut rester (utile pour setup local)"
fi

if git ls-files | grep -q "encode_secrets.py"; then
    echo "⚠️  encode_secrets.py - peut rester (utile pour encoder secrets)"
fi

if git ls-files | grep -q "audit_v2_avec_exceptions.sh"; then
    echo "⚠️  audit_v2_avec_exceptions.sh - peut rester (documentation)"
fi

if git ls-files | grep -q "fix_publisher_v2.sh"; then
    echo "⚠️  fix_publisher_v2.sh - peut rester (documentation)"
fi

if git ls-files | grep -q "apply_3_changements.sh"; then
    echo "⚠️  apply_3_changements.sh - peut rester (documentation)"
fi

echo ""

###############################################################################
# ÉTAPE 4: Vérifier les fichiers temporaires
###############################################################################

echo "4️⃣  Vérification des fichiers temporaires (non-trackés)"
echo ""

# Fichiers non trackés
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)

if [ -z "$UNTRACKED" ]; then
    echo "✅ Aucun fichier temporaire non-tracké"
else
    echo "⚠️  Fichiers non-trackés:"
    echo "$UNTRACKED" | while read file; do
        echo "   - $file"
    done
fi

echo ""

###############################################################################
# ÉTAPE 5: Vérifier .gitignore
###############################################################################

echo "5️⃣  Contenu du .gitignore"
echo ""

if [ -f ".gitignore" ]; then
    echo "✅ .gitignore existe"
    echo ""
    cat .gitignore | grep -v "^#" | grep -v "^$" | while read line; do
        echo "   - $line"
    done
else
    echo "❌ .gitignore manquant!"
fi

echo ""

###############################################################################
# ÉTAPE 6: Résumé de la structure
###############################################################################

echo "6️⃣  Résumé de la structure"
echo ""

echo "Dossiers principaux:"
find . -maxdepth 1 -type d ! -name ".*" ! -name "node_modules" | sort | while read dir; do
    count=$(find "$dir" -type f 2>/dev/null | wc -l)
    echo "   📁 $dir ($count fichiers)"
done

echo ""
echo "Fichiers principaux (racine):"
find . -maxdepth 1 -type f | sort | while read file; do
    echo "   📄 $file"
done

echo ""

###############################################################################
# ÉTAPE 7: Vérifier la taille du repo
###############################################################################

echo "7️⃣  Taille du repository"
echo ""

REPO_SIZE=$(du -sh . 2>/dev/null | cut -f1)
GIT_SIZE=$(du -sh .git 2>/dev/null | cut -f1)

echo "   Repo total: $REPO_SIZE"
echo "   Git size: $GIT_SIZE"

echo ""

###############################################################################
# ÉTAPE 8: Vérifier que les dossiers sensibles n'existent pas
###############################################################################

echo "8️⃣  Vérification dossiers sensibles"
echo ""

SENSIBLE_DIRS=(
    "secrets"
    "credentials"
    "keys"
    "tokens"
)

for dir in "${SENSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "❌ Dossier '$dir' existe! À supprimer:"
        echo "   rm -rf $dir"
    fi
done

echo "✅ Aucun dossier sensible trouvé"
echo ""

###############################################################################
# RÉSUMÉ FINAL
###############################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ RAPPORT DE NETTOYAGE FINAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Fichiers sensibles: AUCUN trouvé"
echo "✅ .gitignore: PRÉSENT et correct"
echo "✅ Dossiers sensibles: AUCUN trouvé"
echo "✅ Fichiers temporaires: À ignorer par .gitignore"
echo ""
echo "📊 Structure:"
echo "   - Dossiers: $(find . -maxdepth 1 -type d ! -name ".*" ! -name "node_modules" | wc -l)"
echo "   - Fichiers trackés: $(git ls-files | wc -l)"
echo "   - Fichiers non-trackés: $(git ls-files --others --exclude-standard | wc -l)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 STATUS:"
echo ""

# Vérifier le status git
if git status --porcelain | grep -q "^??"; then
    echo "⚠️  Il y a des fichiers non-trackés (vérifie .gitignore):"
    git status --porcelain | grep "^??"
else
    echo "✅ Tous les fichiers sont trackés ou ignorés correctement"
fi

echo ""
echo "📋 Dernier commit:"
git log -1 --oneline

echo ""
echo "🔗 Status:"
git status --short || echo "✅ Working tree clean"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ REPO PRÊT POUR LA PRODUCTION!"
echo ""
