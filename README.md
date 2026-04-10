# Auto-Publisher V2

**Auto-Publisher V2** est un pipeline d’automatisation de publication vidéo conçu pour fonctionner de manière autonome via **GitHub Actions**.

Ce système récupère des vidéos stockées sur **Google Drive**, génère des **métadonnées dynamiques** (titres et descriptions) à partir de fichiers locaux, les publie sur **YouTube** ou **TikTok** via leurs API respectives, puis enregistre l’historique des publications dans **Supabase** afin de garantir l’**idempotence** et d’éviter les doublons.

---

## Sommaire

- [Architecture et fonctionnalités](#architecture-et-fonctionnalités)
- [Prérequis](#prérequis)
- [Installation et configuration locale](#installation-et-configuration-locale)
  - [1. Clonage et dépendances](#1-clonage-et-dépendances)
  - [2. Configuration de la base de données Supabase](#2-configuration-de-la-base-de-données-supabase)
  - [3. Authentification Google Drive](#3-authentification-google-drive)
  - [4. Authentification YouTube API (OAuth 2.0)](#4-authentification-youtube-api-oauth-20)
  - [5. Encodage des secrets en Base64](#5-encodage-des-secrets-en-base64)
- [Déploiement GitHub Actions](#déploiement-github-actions)
- [Déployer une nouvelle chaîne (multi-bot)](#déployer-une-nouvelle-chaîne-multi-bot)
- [Dépannage et erreurs fréquentes](#dépannage-et-erreurs-fréquentes)
- [Signature](#signature)

---

## Architecture et fonctionnalités

- **Exécution cloud-native** : le script est déclenché par des workflows `cron` via GitHub Actions, sans nécessiter d’infrastructure locale.
- **Scalabilité multi-comptes** : l’architecture permet de gérer un nombre indéfini de chaînes YouTube ou TikTok en parallèle grâce à des fichiers de configuration JSON et des workflows isolés.
- **Génération dynamique de métadonnées** : les titres et descriptions sont extraits aléatoirement depuis une base textuelle locale afin d’optimiser le SEO et de limiter les comportements répétitifs.
- **Synchronisation Google Drive** : les vidéos sont téléchargées automatiquement via l’API Google Drive à l’aide d’un **Service Account**.
- **Traçabilité Supabase** : chaque vidéo publiée est enregistrée dans une base PostgreSQL distante pour empêcher toute republication involontaire.
- **Monitoring** : les statuts d’exécution (succès, échec, alertes) sont envoyés en temps réel via des webhooks Discord.
- **Comportement anti-bot** : un délai d’exécution aléatoire (`sleep`) peut être appliqué pour simuler un comportement plus humain.

---

## Prérequis

Avant de commencer, assurez-vous de disposer de :

1. **Python 3.11** ou supérieur
2. Un projet **Google Cloud** avec les API suivantes activées :
   - Google Drive API
   - YouTube Data API v3
3. Un projet **Supabase** actif
4. Un **webhook Discord** valide

---

## Installation et configuration locale

### 1. Clonage et dépendances

```bash
git clone <URL_DU_DEPOT>
cd Publisher-v2
pip install -r requirements.txt
```

### 2. Configuration de la base de données Supabase

Dans votre projet Supabase, créez une table nommée `published_videos` avec le schéma suivant :

- `id` : `int8` — clé primaire, auto-incrémentée
- `account_id` : `text`
- `video_id` : `text`
- `platform` : `text`
- `published_at` : `timestamptz` — valeur par défaut : `now()`

Cette table permet de tracer les vidéos déjà publiées et d’éviter les doublons.

### 3. Authentification Google Drive

1. Générez une clé JSON pour un **Service Account** depuis Google Cloud.
2. Partagez les dossiers Google Drive cibles avec l’adresse e-mail de ce compte de service.
3. Accordez-lui les droits nécessaires au téléchargement des fichiers.

### 4. Authentification YouTube API (OAuth 2.0)

L’authentification YouTube nécessite une **initialisation manuelle locale** afin de générer le token OAuth.

#### Étapes

1. Créez des identifiants **OAuth 2.0** de type **Application de bureau** dans Google Cloud.
2. Téléchargez le fichier sous le nom :

```text
secrets/<NOM_COMPTE>_client_secrets.json
```

3. Placez une vidéo factice nommée `test.mp4` à la racine du projet.
4. Exécutez la commande suivante :

```bash
youtube-upload --client-secrets="secrets/<NOM_COMPTE>_client_secrets.json" --credentials-file="secrets/<NOM_COMPTE>_credentials.json" --title="Test Auth" --privacy="private" test.mp4
```

5. Suivez le lien affiché dans le terminal.
6. Connectez-vous avec le compte YouTube cible.
7. Autorisez l’application.

Une fois l’opération terminée, le fichier suivant sera généré :

```text
secrets/<NOM_COMPTE>_credentials.json
```

### 5. Encodage des secrets en Base64

GitHub Actions nécessite souvent l’injection des fichiers JSON via des variables d’environnement textuelles. Pour cela, encodez vos fichiers en **Base64**.

Exemple en PowerShell :

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("chemin\vers\fichier.json"))
```

Répétez cette opération pour chaque fichier JSON à stocker dans les secrets GitHub.

---

## Déploiement GitHub Actions

Dans votre dépôt GitHub, rendez-vous dans :

**Settings > Secrets and variables > Actions**

Ajoutez les secrets suivants :

- `SUPABASE_URL` : URL de votre instance Supabase
- `SUPABASE_KEY` : clé publique (`anon`) Supabase
- `DISCORD_WEBHOOK_URL` : URL du webhook Discord
- `GDRIVE_SA_JSON_B64` : fichier JSON du Service Account Drive encodé en Base64
- `YT_CLIENT_SECRETS_B64` : fichier `client_secrets.json` encodé en Base64
- `YT_CREDENTIALS_B64` : fichier `credentials.json` encodé en Base64
- `DRIVE_FOLDER_ID` : ID du dossier Google Drive cible

---

## Déployer une nouvelle chaîne (multi-bot)

Pour ajouter une nouvelle chaîne ou un nouveau compte de publication :

1. Dupliquez `config/youtube_compte1.json` vers un nouveau fichier, par exemple :

```text
config/youtube_compte2.json
```

2. Adaptez les métadonnées à la nouvelle chaîne.
3. Ajoutez un nouveau fichier texte de descriptions dans :

```text
content/descriptions/
```

4. Générez un nouveau fichier OAuth `credentials.json` localement.
5. Encodez-le en Base64.
6. Ajoutez-le comme nouveau secret GitHub, par exemple :

```text
YT_CREDENTIALS_COMPTE2_B64
```

7. Dupliquez le workflow existant, par exemple :

```text
.github/workflows/publisher.yml
```

8. Mettez à jour les variables d’environnement ciblées :
   - `ACCOUNT_NAME`
   - `DRIVE_FOLDER_ID`
   - `YT_CREDENTIALS_B64`

Cette approche permet d’isoler chaque bot tout en conservant une architecture modulaire et scalable.

---

## Dépannage et erreurs fréquentes

### Erreur : `Error 403: access_denied` lors de l’authentification YouTube

**Cause**  
L’application OAuth Google Cloud est en mode **Test** et l’adresse e-mail du compte YouTube n’a pas été autorisée.

**Solution**  
Dans Google Cloud, ouvrez :

**API et services > Écran de consentement OAuth**

Puis, dans la section **Utilisateurs tests**, ajoutez l’adresse e-mail du compte YouTube concerné.

---

### Erreur : `FileNotFoundError: [Errno 2] No such file or directory: 'test.mp4'`

**Cause**  
La bibliothèque `youtube-upload` exige la présence d’un fichier vidéo réel pour finaliser la création du token OAuth.

**Solution**  
Placez n’importe quelle vidéo `.mp4` nommée `test.mp4` à la racine du projet avant d’exécuter la commande d’authentification.

---

### Erreur GitHub Actions : configuration introuvable (`config/youtube_compteX.json`)

**Cause**  
Le fichier de configuration n’a pas été poussé sur le dépôt distant, souvent à cause d’une règle dans le `.gitignore`.

**Solution**

```bash
git add -f config/youtube_compteX.json
git commit -m "Force l'ajout de la configuration"
git push
```

---

### La description par défaut `Shorts` s’affiche au lieu du texte prévu

**Cause**  
Le chemin vers le fichier texte défini dans le JSON est incorrect, ou le fichier n’a pas été poussé sur GitHub à cause d’une règle `.gitignore`.

**Solution**

1. Vérifiez que la clé `descriptions_file` du fichier JSON pointe exactement vers le bon chemin.
2. Forcez l’ajout du fichier texte :

```bash
git add -f content/descriptions/nomdufichier.txt
git commit -m "Ajout forcé du fichier de description"
git push
```

---

## Signature

```text
  ____       _      __     __  ___   _   _      _    
 / ___|     / \     \ \   / / |_ _| | \ | |    / \   
 \___ \    / _ \     \ \ / /   | |  |  \| |   / _ \  
  ___) |  / ___ \     \ V /    | |  | |\  |  / ___ \ 
 |____/  /_/   \_\     \_/    |___| |_| \_| /_/   \_\
                                                     
                                 Created by SAVINA
```
