================================================================================

    ██████╗ ██╗   ██╗██████╗ ██╗     ██╗███████╗██╗  ██╗███████╗██████╗ 
    ██╔══██╗██║   ██║██╔══██╗██║     ██║██╔════╝██║  ██║██╔════╝██╔══██╗
    ██████╔╝██║   ██║██████╔╝██║     ██║███████╗███████║█████╗  ██████╔╝
    ██╔═══╝ ██║   ██║██╔══██╗██║     ██║╚════██║██╔══██║██╔══╝  ██╔══██╗
    ██║     ╚██████╔╝██████╔╝███████╗██║███████║██║  ██║███████╗██║  ██║
    ╚═╝      ╚═════╝ ╚═════╝ ╚══════╝╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                          
                          V E R S I O N   2 . 0   T I T A N

    Multi-Platform Video Publisher with Anti-Shadowban Protection
    
    Created by:    heydanio
    Version:       2.0.0 TITAN
    License:       MIT
    Status:        Production Ready

================================================================================


TABLE OF CONTENTS

    1.  Overview & Features
    2.  Architecture
    3.  Quick Start
    4.  Multi-Account Setup (Scalable to 100+ accounts)
    5.  Anti-Shadowban Protection
    6.  Database Setup
    7.  GitHub Secrets
    8.  Running the System
    9.  Adding New Accounts
    10. TikTok Fork Setup (Important!)
    11. Configuration Reference
    12. Monitoring
    13. Troubleshooting
    14. Performance
    15. Costs


================================================================================
1. OVERVIEW & FEATURES
================================================================================

Production-grade automated video publishing system with built-in
anti-shadowban protection and infinite multi-account scalability.

Core Features:
    - Multi-platform: YouTube + TikTok
    - Infinite multi-account scaling (matrix strategy)
    - Anti-shadowban rate limiting
    - Content validation (anti-spam)
    - Idempotent operations (no duplicates)
    - Human-like behavior simulation
    - Discord notifications with rich embeds
    - Comprehensive logging and monitoring
    - Zero infrastructure costs

Anti-Shadowban Features:
    - Max uploads per day (configurable per account)
    - Min gap between uploads (configurable)
    - Max uploads per hour
    - Random delays with Gaussian distribution
    - Tag/title validation against spam patterns
    - Content sanitization (zero-width chars, etc.)
    - Pinned dependencies (supply chain security)


================================================================================
2. ARCHITECTURE
================================================================================

High-Level Flow:

    GitHub Actions Cron (Matrix Strategy)
            |
            v
    For each account in matrix:
            |
            +-- Load config (config/account.json)
            |
            +-- Check rate limits (anti-shadowban)
            |       |
            |       +-- BLOCKED? -> Skip + Discord notification
            |
            +-- Check schedule (or FORCE_POST)
            |
            +-- Query Supabase (unpublished videos)
            |
            +-- Download from Google Drive
            |
            +-- Validate content (anti-spam)
            |
            +-- Upload to platform
            |
            +-- Record in Supabase (published_videos)
            +-- Record in Supabase (upload_history)
            |
            +-- Send Discord notification


Components:

    src/config.py                Configuration with validation
    src/utils/logger.py          Structured logging
    src/utils/retry.py           Retry decorator
    src/utils/timing.py          Human-like timing (Gaussian)
    src/core/state.py            Supabase state (singleton)
    src/core/drive.py            Drive API (paginated)
    src/core/alert.py            Discord (rich embeds)
    src/core/rate_limiter.py     Anti-shadowban rate limiting
    src/core/safeguards.py       Content validation
    src/platforms/youtube.py     YouTube upload
    src/platforms/tiktok.py      TikTok upload
    src/main.py                  Orchestrator


================================================================================
3. QUICK START
================================================================================

Prerequisites:

    - Python 3.11+
    - GitHub account
    - Supabase account (free tier OK)
    - Google Cloud account


Installation:

    $ git clone https://github.com/heydanio/Publisher-v2.git
    $ cd Publisher-v2
    $ make install


Setup (3 steps):

    1. Fork TiktokAutoUploader (see Section 10)
    2. Create Supabase tables (see Section 6)
    3. Add GitHub Secrets (see Section 7)


================================================================================
4. MULTI-ACCOUNT SETUP (SCALABLE)
================================================================================

The system uses GitHub Actions matrix strategy.
You can add UNLIMITED accounts by modifying the matrix.

YouTube Accounts in .github/workflows/youtube.yml:

    matrix:
      account:
        - youtube_compte1
        - youtube_compte2
        - youtube_compte3
        - youtube_compte_N

Each account needs:
    1. Config file: config/youtube_compteN.json
    2. Entry in matrix (1 line)
    3. Same GitHub Secrets (shared)


TikTok Accounts in .github/workflows/tiktok.yml:

    matrix:
      account:
        - tiktok_1
        - tiktok_2
        - tiktok_N

Each TikTok account needs:
    1. Config file: config/tiktok_N.json
    2. Entry in matrix
    3. Specific cookies secret: TIKTOK_COOKIES_TIKTOK_N


Sequential Execution:
    
    The matrix runs accounts SEQUENTIALLY (max-parallel: 1)
    to avoid:
        - Drive API rate limiting
        - YouTube account-switching detection
        - TikTok IP-based detection


================================================================================
5. ANTI-SHADOWBAN PROTECTION
================================================================================

This is the most important feature for serious creators.

The system enforces 3 layers of protection:


Layer 1: Rate Limiting (per account, per platform)

    YouTube defaults:
        - Max 3 uploads per day
        - Min 60 minutes between uploads
        - Max 1 upload per hour

    TikTok defaults:
        - Max 4 uploads per day
        - Min 45 minutes between uploads
        - Max 1 upload per hour

    Custom per account in config/account.json:
    
    {
        "rate_limit": {
            "max_per_day": 5,
            "min_gap_minutes": 30,
            "max_per_hour": 2
        }
    }


Layer 2: Content Validation

    Automatic rejection of:
        - Spam tags (#follow4follow, #l4l, etc.)
        - All-caps titles (>70% uppercase)
        - Excessive punctuation (!!!, ???)
        - Spam patterns ("YOU WONT BELIEVE", etc.)
        - Duplicate tags
        - Too many hashtags (>30 in description)

    Automatic sanitization of:
        - Zero-width spaces
        - Multiple whitespaces
        - Invisible Unicode characters


Layer 3: Human-Like Behavior

    - Random delays with Gaussian distribution (not uniform)
    - Variance of 30-50% around expected delays
    - Realistic user-agents
    - Random minutes within scheduled hours
    - No round-number delays


================================================================================
6. DATABASE SETUP
================================================================================

Run these SQL queries in Supabase (SQL Editor):


Query 1 - Published videos tracking:

    CREATE TABLE IF NOT EXISTS published_videos (
        id BIGSERIAL PRIMARY KEY,
        account_name TEXT NOT NULL,
        drive_file_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        published_at TIMESTAMPTZ DEFAULT NOW(),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    CREATE UNIQUE INDEX idx_pub_videos_unique
    ON published_videos(account_name, drive_file_id, platform);


Query 2 - Upload history (anti-shadowban):

    CREATE TABLE IF NOT EXISTS upload_history (
        id BIGSERIAL PRIMARY KEY,
        account_name TEXT NOT NULL,
        platform TEXT NOT NULL,
        uploaded_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    CREATE INDEX idx_upload_history_account_time
    ON upload_history(account_name, uploaded_at DESC);


You can also run: make migrate (shows the SQL)


================================================================================
7. GITHUB SECRETS
================================================================================

Location: Settings > Secrets and variables > Actions


Common Secrets (all accounts):

    SUPABASE_URL                  Supabase project URL
    SUPABASE_KEY                  Supabase API key
    DRIVE_FOLDER_ID               Default Drive folder ID
    DISCORD_WEBHOOK_URL           Discord webhook
    GDRIVE_SA_JSON_B64            Service account JSON (base64)


YouTube-specific:

    YT_CLIENT_SECRETS_B64         OAuth client secrets (base64)
    YT_CREDENTIALS_B64            OAuth credentials (base64)


TikTok-specific (one per account):

    TIKTOK_BROWSER_JS_B64         Signature code (base64)
    TIKTOK_COOKIES_TIKTOK_1       Cookies for account 1
    TIKTOK_COOKIES_TIKTOK_2       Cookies for account 2
    (etc.)


================================================================================
8. RUNNING THE SYSTEM
================================================================================

Automatic (cron):

    Workflows run automatically:
        9:00, 12:00, 15:00, 17:00, 20:00 (Paris time)
    
    Each cron triggers ALL accounts in matrix (sequentially).


Manual (single account):

    Repository > Actions > YouTube Publisher > Run workflow
        Account: youtube_compte2  (or blank for all)
        Force post: true


Local Testing:

    $ export ACCOUNT_NAME=youtube_compte1
    $ export FORCE_POST=1
    $ export DRIVE_FOLDER_ID=...
    $ make run


================================================================================
9. ADDING NEW ACCOUNTS
================================================================================

Adding a new YouTube account (5 minutes):

    1. Create config/youtube_compte3.json:
    
       {
         "platform": "youtube",
         "account_id": "UC_xxxxxxx",
         "drive_folder_ids": ["folder_id"],
         "schedule": {
           "slots_hours": [9, 14, 19]
         },
         "content": {
           "descriptions_file": "content/descriptions/MyChannel.txt",
           "tags_pool": ["#shorts", "#viral"],
           "youtube_category": "Entertainment"
         },
         "rate_limit": {
           "max_per_day": 2
         }
       }
    
    2. Add to matrix in .github/workflows/youtube.yml:
    
       matrix:
         account:
           - youtube_compte1
           - youtube_compte2
           - youtube_compte3   # <-- NEW LINE!
    
    3. Commit and push:
    
       $ git add config/youtube_compte3.json .github/workflows/youtube.yml
       $ git commit -m "feat: add youtube_compte3"
       $ git push
    
    Done! The new account is now active.


Adding a new TikTok account:

    1. Create config/tiktok_3.json (with platform: tiktok)
    2. Add to .github/workflows/tiktok.yml matrix
    3. Add secret TIKTOK_COOKIES_TIKTOK_3
    4. Add env line in workflow for the new secret
    5. Commit and push


================================================================================
10. TIKTOK FORK SETUP (IMPORTANT!)
================================================================================

To eliminate external dependencies, you MUST fork TiktokAutoUploader:

Step 1: Fork the repo

    1. Go to: https://github.com/makiisthenes/TiktokAutoUploader
    2. Click "Fork" button (top right)
    3. Select your account (heydanio)
    4. Wait for fork to complete
    
    Your fork will be at: https://github.com/heydanio/TiktokAutoUploader


Step 2: Verify the workflow

    The file .github/workflows/tiktok.yml already references:
        repository: heydanio/TiktokAutoUploader
    
    If your username differs, edit this line.


Step 3: Optional - Pin to specific SHA

    For maximum security, pin to a specific commit:
    
    repository: heydanio/TiktokAutoUploader
    ref: 73475dbb67be5d8e5e7181af665fbf7f0db7fff4


Benefits of forking:
    - No external dependency
    - You control updates
    - Protection from supply chain attacks
    - Repo cannot disappear


================================================================================
11. CONFIGURATION REFERENCE
================================================================================

Complete config/account.json reference:

    {
      "platform": "youtube",                    // or "tiktok"
      "account_id": "UC_xxxx" or "username",
      "drive_folder_ids": ["folder1", "folder2"],
      "schedule": {
        "slots_hours": [9, 12, 15, 17, 20]
      },
      "content": {
        "descriptions_file": "content/file.txt",
        "tags_pool": ["#tag1", "#tag2"],
        "youtube_category": "Entertainment"     // YouTube only
      },
      "tags": ["#fyp", "#viral"],               // TikTok only
      "rate_limit": {
        "max_per_day": 3,                       // optional
        "min_gap_minutes": 60,                  // optional
        "max_per_hour": 1                       // optional
      }
    }


================================================================================
12. MONITORING
================================================================================

Discord Notifications:

    Success: Green/Red/Black embed with platform info
    Error: Red embed with error details
    Rate Limit: Orange embed (helps you tune limits)

GitHub Actions:

    Repository > Actions
    Each matrix run shown as separate job
    Look for "[OK]" and "FAIL" in logs

Supabase queries:

    -- Recent publications
    SELECT * FROM published_videos
    ORDER BY created_at DESC LIMIT 20;
    
    -- Upload history (rate limiting)
    SELECT account_name, platform, uploaded_at
    FROM upload_history
    WHERE uploaded_at > NOW() - INTERVAL '24 hours'
    ORDER BY uploaded_at DESC;
    
    -- Stats per account (last 30 days)
    SELECT account_name, platform, COUNT(*) as total
    FROM published_videos
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY account_name, platform
    ORDER BY total DESC;


================================================================================
13. TROUBLESHOOTING
================================================================================

"Rate limit atteinte"
    
    Normal! C'est l'anti-shadowban qui protege.
    Vérifie tes limites dans config/account.json
    Si trop strictes, augmente max_per_day


"Aucune video disponible"

    - Toutes les videos sont deja publiees (normal)
    - Verifier que des videos sont dans le dossier Drive
    - Vérifier que published_videos table n'a pas trop d'entrées


"Tags spammy detectes"

    Le validator a rejeté tes tags.
    Enlève les tags spammy (#l4l, #follow4follow, etc.)


"TIKTOK_COOKIES_X manquant"

    Ajoute le secret correspondant au compte.
    Format: TIKTOK_COOKIES_<ACCOUNT_NAME_UPPER>


"upstream/cli.py introuvable"

    Tu n'as pas forké TiktokAutoUploader (voir section 10)


================================================================================
14. PERFORMANCE
================================================================================

Per-Run Timing:

    GitHub Actions startup    30s
    Dependency install        10s (cached)
    Random delay              60-600s
    Drive download            30-60s
    Content validation         1s
    Upload to platform        60-180s
    State management           5s
    Discord notification       1s
    
    Total per account:        ~3-15 minutes


Resource Usage:

    Per account per day:    ~10-15 minutes GitHub Actions
    For 5 accounts:         ~50-75 min/day = ~1500-2250 min/month
    
    GitHub Actions free:    2000 minutes/month
    Recommendation:         Max 5-7 accounts on free tier


================================================================================
15. COSTS
================================================================================

Monthly Cost: $0 USD

    Service           Cost  Notes
    -------           ----  -----
    GitHub Actions    FREE  2000 min/month
    Supabase          FREE  Generous free tier
    Google Drive      FREE  Personal account
    YouTube           FREE  Personal channels
    TikTok            FREE  Personal accounts
    Discord           FREE  Webhooks free

For more than 7 accounts:
    - Consider GitHub Pro ($4/month for 3000 min)
    - Or self-host on a $5/month VPS


================================================================================

                            Built with passion
                                by heydanio

                          For support and updates:
              https://github.com/heydanio/Publisher-v2/issues

================================================================================
