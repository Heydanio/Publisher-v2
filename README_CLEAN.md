================================================================================

     ___    _   _____ ___       ____        _     _ _     _              
    / _ |  | | |_   _/ _ \     |  _ \ _   _| |__ | (_)___| |__   ___ _ __ 
   / / | |_| |   | || | | |    | |_) | | | | '_ \| | / __| '_ \ / _ \ '__|
  / /  | |_   _|  | || |_| |    |  __/| |_| | |_) | | \__ \ | | |  __/ |   
 /_/   |_| |_|    |_| \___/     |_|    \__,_|_.__/|_|_|___/_| |_|\___|_|   
                                                                             

  Automated Video Publishing System
  YouTube | TikTok | Google Drive
  
  Created by: heydanio
  Version: 2.0
  License: MIT

================================================================================


TABLE OF CONTENTS

1.  Overview
2.  Features
3.  Technical Stack
4.  Project Structure
5.  Installation & Setup
6.  Configuration
7.  GitHub Secrets
8.  Supabase Database
9.  Running the System
10. Security
11. Monitoring & Logs
12. Troubleshooting
13. Costs
14. Contributing


================================================================================
1. OVERVIEW
================================================================================

Auto-Publisher V2 is an automated video publishing system that uploads videos
from Google Drive to YouTube and TikTok on a scheduled basis using GitHub
Actions as the orchestration layer.

Key Principles:
- Zero cost infrastructure (using free tiers only)
- Idempotent operations (no duplicate publications)
- Fully automated scheduling
- Comprehensive monitoring via Discord webhooks
- Secure credential management


================================================================================
2. FEATURES
================================================================================

Core Features:
  - Multi-platform support (YouTube, TikTok)
  - Scheduled publication via GitHub Actions cron
  - Automatic state management with Supabase
  - Anti-detection mechanisms (random delays, human-like behavior)
  - Real-time notifications via Discord
  - Idempotent operations (guaranteed no re-publications)
  - Multi-account support per platform

Advanced Features:
  - Random delay injection (5-10 minutes)
  - Automatic pip cache (90 seconds saved per run)
  - Optimized database queries
  - Pre-commit hooks for security


================================================================================
3. TECHNICAL STACK
================================================================================

Orchestration:
  GitHub Actions (free tier: 2000 minutes/month)

Storage & API:
  Google Drive API (video source)
  Supabase PostgreSQL (publication state)

Publishing:
  YouTube: youtube-upload CLI (v0.8.1 pinned)
  TikTok: Selenium + undetected-chromedriver

Notifications:
  Discord Webhooks (real-time status)

Runtime:
  Python 3.11
  Dependencies: see requirements.txt


================================================================================
4. PROJECT STRUCTURE
================================================================================

Publisher-v2/
|
+-- .github/
|   +-- workflows/
|       +-- publisher.yml        [YouTube automation]
|       +-- tiktok_1.yml         [TikTok automation]
|       +-- youtube_2.yml        [Account 2 automation]
|       +-- keep_alive.yml       [Periodic heartbeat]
|
+-- src/
|   +-- main.py                  [Entry point]
|   +-- core/
|   |   +-- state.py             [Supabase state management]
|   |   +-- drive.py             [Google Drive API client]
|   |   +-- alert.py             [Discord notifications]
|   +-- platforms/
|       +-- youtube.py           [YouTube upload logic]
|       +-- tiktok.py            [TikTok upload logic]
|
+-- config/                      [Local configuration - NOT tracked]
|   +-- youtube_compte1.json     [Account 1 config]
|   +-- tiktok_1.json            [TikTok account config]
|
+-- content/
|   +-- descriptions/            [Video descriptions]
|       +-- BREAKKINGROT.txt
|       +-- CHAsderion.txt
|
+-- requirements.txt             [Python dependencies]
+-- .gitignore                   [Security-first ignore rules]
+-- README.md                    [This file]


================================================================================
5. INSTALLATION & SETUP
================================================================================

Step 1: Clone the Repository

  $ git clone https://github.com/heydanio/Publisher-v2.git
  $ cd Publisher-v2


Step 2: Install Python Dependencies

  $ pip install -r requirements.txt

  Core packages installed:
  - requests (HTTP client)
  - google-api-python-client (Drive & YouTube API)
  - supabase (Database client)
  - selenium (TikTok automation)
  - undetected-chromedriver (Anti-detection)


Step 3: Create Local Configuration Directory

  $ mkdir -p config/

  Note: Configuration files are NEVER committed to Git.
  They contain sensitive account information (IDs, credentials).


Step 4: Configure Your Accounts

  Create config/youtube_compte1.json:

  {
    "platform": "youtube",
    "account_id": "UC_YOUR_CHANNEL_ID",
    "drive_folder_ids": ["FOLDER_ID_1", "FOLDER_ID_2"],
    "schedule": {
      "slots_hours": [9, 12, 15, 17, 20]
    }
  }

  Create config/tiktok_1.json:

  {
    "platform": "tiktok",
    "account_id": "your_tiktok_username",
    "drive_folder_ids": ["FOLDER_ID"],
    "schedule": {
      "slots_hours": [9, 12, 15, 17, 20]
    }
  }


================================================================================
6. CONFIGURATION
================================================================================

Account Configuration (local files, NOT tracked):

  platform:           "youtube" or "tiktok"
  account_id:         Your YouTube channel ID or TikTok username
  drive_folder_ids:   Array of Google Drive folder IDs (video sources)
  schedule.slots_hours: Array of hours to publish (24-hour format, UTC+2)


Schedule Examples:

  France (UTC+2):
  [9, 12, 15, 17, 20] publishes at 9:00, 12:00, 15:00, 17:00, 20:00

  Publishing happens only if:
  - Current hour matches a scheduled hour
  - Current minute is less than 55
  - An unpublished video exists in the folder


Folder Structure Expectations:

  Google Drive Folder/
  ├─ video1.mp4       (with description in filename or metadata)
  ├─ video2.mp4
  └─ ...

  First unpublished video (alphabetically) gets uploaded.


================================================================================
7. GITHUB SECRETS
================================================================================

All credentials must be stored as GitHub Secrets (encrypted at rest).

Location: Repository Settings > Secrets and variables > Actions


Secrets to Configure:

  GDRIVE_SA_JSON_B64
    Type: Google Service Account JSON (base64 encoded)
    Purpose: Read access to Google Drive
    Format: base64 of service_account.json

  YT_CLIENT_SECRETS_B64
    Type: YouTube OAuth client secrets (base64 encoded)
    Purpose: YouTube API authentication
    Format: base64 of client_secret.json

  YT_CREDENTIALS_B64
    Type: YouTube OAuth user credentials (base64 encoded)
    Purpose: YouTube upload authorization
    Format: base64 of credentials.json

  TIKTOK_BROWSER_JS_B64
    Type: TikTok request signature code (base64 encoded)
    Purpose: TikTok request signing
    Format: base64 of browser signature code

  DRIVE_FOLDER_ID
    Type: Plain text (not base64)
    Purpose: Root folder ID for video source
    Format: "1ABC_DEFG_HIJKLMNOP"

  SUPABASE_URL
    Type: Plain text
    Purpose: Supabase instance URL
    Format: "https://xxxxx.supabase.co"

  SUPABASE_KEY
    Type: Plain text
    Purpose: Supabase API key
    Format: "eyJhbGc..."

  DISCORD_WEBHOOK_URL
    Type: Plain text
    Purpose: Discord notifications
    Format: "https://discordapp.com/api/webhooks/..."


Encoding Base64 (local, never commit):

  Linux/Mac:
  $ base64 -i service_account.json

  Windows PowerShell:
  $ [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("file.json"))


================================================================================
8. SUPABASE DATABASE
================================================================================

Create the Published Videos Table:

  SQL Query:

  CREATE TABLE published_videos (
    id BIGSERIAL PRIMARY KEY,
    account_name TEXT NOT NULL,
    drive_file_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    published_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE UNIQUE INDEX idx_pub_videos_unique
  ON published_videos(account_name, drive_file_id, platform);

  CREATE INDEX idx_pub_videos_account
  ON published_videos(account_name);

  CREATE INDEX idx_pub_videos_platform
  ON published_videos(platform);


Purpose:

  This table tracks which videos have been published to which platforms
  under which accounts. It provides idempotence guarantees.

  Before uploading, the system queries:
  SELECT COUNT(*) FROM published_videos 
  WHERE account_name = ? AND drive_file_id = ? AND platform = ?

  If count > 0, the video is already published and skipped.


================================================================================
9. RUNNING THE SYSTEM
================================================================================

Automatic Execution (via GitHub Actions):

  The system runs automatically according to the cron schedule defined in
  .github/workflows/publisher.yml:

  Schedule: 0 8,11,14,16,19 * * *
  (UTC times, which are 9:00, 12:00, 15:00, 17:00, 20:00 in Paris/UTC+1)

  Each run:
  1. Fetches unpublished videos from Google Drive
  2. Downloads the first unpublished video
  3. Uploads to the target platform (YouTube or TikTok)
  4. Records in Supabase publication_videos table
  5. Sends Discord notification with status


Manual Trigger (via GitHub Web Interface):

  Repository > Actions > Select Workflow > Run workflow

  This forces immediate execution regardless of schedule.


Local Testing:

  $ export ACCOUNT_NAME="youtube_compte1"
  $ export FORCE_POST="1"
  $ export DRIVE_FOLDER_ID="your_folder_id"
  $ export GDRIVE_SA_JSON_B64="your_base64"
  $ export SUPABASE_URL="your_url"
  $ export SUPABASE_KEY="your_key"
  $ export DISCORD_WEBHOOK_URL="your_webhook"
  $ python src/main.py

  Note: Environment variables can be set in .env (local, not tracked)


================================================================================
10. SECURITY
================================================================================

Design Principles:

  1. Zero Secrets in Code
     - All credentials stored in GitHub Secrets
     - Configuration files (.json) never committed
     - Base64 encoding for binary data

  2. Pre-commit Hooks
     - Automatic validation of attempted commits
     - Prevents accidental credential exposure
     - Runs on: git commit

  3. Strict .gitignore
     Rules enforce:
     - No *.json files in repo
     - No .env or .env.local
     - No secrets/ directory
     - No *.key or *.pem files

  4. Idempotent Operations
     - Database uniqueness constraint prevents re-uploads
     - If operation fails, state remains consistent
     - Safe to retry manually

  5. Encrypted Credentials
     - GitHub Secrets encrypted at rest
     - Base64 encoding (not encryption) for transport
     - Final decoding happens only in GitHub Actions runners


Files Never Committed:

  config/
  secrets/
  .env
  *.json (except package.json)
  *.key
  *.pem
  OAuth credentials
  Service accounts


Pre-commit Hook (.git/hooks/pre-commit):

  Automatically blocks commits containing:
  - secrets/
  - .env
  - client_secret
  - credentials.json
  - token.json


================================================================================
11. MONITORING & LOGS
================================================================================

Discord Notifications:

  Every upload generates a Discord message:

  Success Format:
    PUBLICATION SUCCESSFUL (YOUTUBE)
    Account: youtube_compte1
    Video: My Video Title
    Time: 09:30 Paris Time

  Failure Format:
    PUBLICATION FAILED
    Account: youtube_compte1
    Error: [Error details]


GitHub Actions Logs:

  View execution logs:
  Repository > Actions > [Workflow Name] > [Run] > [Job]

  Logs include:
  - Step-by-step execution trace
  - File downloads and uploads
  - API responses
  - Error messages
  - Timing information


Supabase Console:

  Query publication history:

  SELECT * FROM published_videos
  WHERE account_name = 'youtube_compte1'
  ORDER BY created_at DESC
  LIMIT 10;

  This shows:
  - Account name
  - Drive file ID
  - Platform (youtube/tiktok)
  - Publication timestamp
  - Creation timestamp


Performance Monitoring:

  GitHub Actions Dashboard shows:
  - Total run time (target: 2-3 minutes)
  - Success/failure rate
  - Run history


================================================================================
12. TROUBLESHOOTING
================================================================================

No Videos Published

  Check:
  1. Unpublished videos exist in Google Drive folder
  2. Current time matches schedule (check UTC vs local time)
  3. DRIVE_FOLDER_ID secret is correct
  4. Google Drive permissions are valid


YouTube Upload Fails

  Check:
  1. YT_CREDENTIALS_B64 is valid and current
  2. Channel is monetized (required by youtube-upload)
  3. OAuth token hasn't expired (refresh by re-authenticating)
  4. Internet connection on runner


TikTok Upload Fails

  Check:
  1. TIKTOK_BROWSER_JS_B64 is recent
  2. Account isn't rate-limited
  3. Video format is supported (MP4, H.264)
  4. Video duration within limits (15 sec - 10 minutes)


Supabase Connection Error

  Check:
  1. SUPABASE_URL secret is set and correct
  2. SUPABASE_KEY secret is set and valid
  3. published_videos table exists
  4. Network connectivity (check GitHub Actions runner logs)


Discord Webhook Fails

  Check:
  1. DISCORD_WEBHOOK_URL is current (webhooks can expire)
  2. Discord channel still exists
  3. Bot still has permission to post


Idempotence Error (Video Already Published)

  This is not an error. It's working correctly.
  The system detected the video is already in published_videos table.

  To re-publish: Delete the record from published_videos manually.


================================================================================
13. COSTS
================================================================================

Infrastructure Costs: $0 USD/month

  GitHub Actions:      Free (2000 min/month - we use ~20 min/month)
  Supabase:            Free Tier (generous limits)
  Google Drive:        Your existing account
  YouTube:             Your existing account
  TikTok:              Your existing account
  Discord:             Free


Total Monthly Cost:

  ZERO

  This project is designed to use only free services.
  Scaling to paid tiers is optional but not necessary.


================================================================================
14. CONTRIBUTING
================================================================================

Code Standards:

  Python:
  - Python 3.11+ required
  - Follow PEP 8 style guide
  - Type hints preferred
  - Docstrings for functions

  Commits:
  - Clear, descriptive messages
  - Reference issues when applicable
  - One feature per commit


Workflow:

  1. Fork the repository
  2. Create a feature branch:
     $ git checkout -b feature/my-feature

  3. Make your changes
  4. Test locally
  5. Commit with clear messages:
     $ git commit -m "feat: description of changes"

  6. Push to your fork:
     $ git push origin feature/my-feature

  7. Create a Pull Request with description


Issue Reporting:

  Include:
  - What you were trying to do
  - What happened
  - What you expected
  - Relevant logs or error messages
  - Your configuration (sanitized)


================================================================================

Created by: heydanio
Version: 2.0
Last Updated: May 2026
License: MIT

For support, issues, or questions:
https://github.com/heydanio/Publisher-v2/issues

================================================================================
