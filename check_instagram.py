"""
VoicePad AI — Instagram & Facebook Integration Diagnostics
Run this script to verify:
1. Facebook Page access and token validity.
2. Linked Instagram Professional (Creator / Business) Account status.
3. Required Instagram publishing permissions (instagram_basic, instagram_content_publish).
4. Audio & FFmpeg configuration for Instagram Reels compatibility.
"""

import os
import sys
import json
import shutil
import subprocess
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

GRAPH_VERSION = 'v21.0'
GRAPH_URL = f'https://graph.facebook.com/{GRAPH_VERSION}'

def check_ffmpeg():
    print("\n[1] Checking FFmpeg & Audio Setup...")
    ffmpeg_ok = shutil.which('ffmpeg') is not None
    ffprobe_ok = shutil.which('ffprobe') is not None
    if ffmpeg_ok and ffprobe_ok:
        print("  [OK] FFmpeg & FFprobe installed.")
    else:
        print(f"  [WARN] FFmpeg found: {ffmpeg_ok}, FFprobe found: {ffprobe_ok}")

    print("  [INFO] Video Audio Specifications for Instagram Reels:")
    print("     - Codec: AAC (-c:a aac)")
    print("     - Sample Rate: 44,100 Hz (-ar 44100) or 48,000 Hz")
    print("     - Channels: Stereo 2-channel (-ac 2)")
    print("     - Bitrate: 128 kbps (-b:a 128k)")
    print("     - Loudness: -16 LUFS (loudnorm)")
    print("     - Format: MP4 with +faststart (moov atom at front)")

def check_meta_connection():
    print("\n[2] Checking Meta Facebook & Instagram Connection...")
    page_id = os.environ.get('FB_PAGE_ID', '').strip()
    page_token = os.environ.get('FB_PAGE_ACCESS_TOKEN', '').strip()
    ig_env_id = os.environ.get('INSTAGRAM_ACCOUNT_ID', '').strip()

    if not page_id or not page_token:
        print("  [ERROR] FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN is missing from your environment / .env!")
        print("     Please set FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN.")
        return

    print(f"  Target Facebook Page ID: {page_id}")
    if ig_env_id:
        print(f"  Configured INSTAGRAM_ACCOUNT_ID in environment: {ig_env_id}")
    else:
        print("  INSTAGRAM_ACCOUNT_ID in environment: (Not set - attempting auto-discovery)")

    # 1. Test Page Details
    try:
        page_url = f"{GRAPH_URL}/{page_id}"
        resp = requests.get(page_url, params={'access_token': page_token, 'fields': 'id,name,link'}, timeout=15)
        if resp.status_code == 200:
            p_data = resp.json()
            print(f"  [OK] Facebook Page Connected: {p_data.get('name')} (ID: {p_data.get('id')})")
        else:
            print(f"  [ERROR] Failed to verify Facebook Page ({resp.status_code}): {resp.text}")
            return
    except Exception as e:
        print(f"  [ERROR] Error contacting Facebook Graph API: {e}")
        return

    # 2. Check Connected Instagram Account
    print("\n[3] Checking Linked Instagram Account on Facebook Page...")
    try:
        ig_query_url = f"{GRAPH_URL}/{page_id}"
        params = {
            'fields': 'instagram_business_account{id,username,name,followers_count},connected_instagram_account{id,username,name}',
            'access_token': page_token
        }
        resp = requests.get(ig_query_url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            ig_bus = data.get('instagram_business_account')
            ig_conn = data.get('connected_instagram_account')

            ig_account = ig_bus or ig_conn
            if ig_account:
                ig_id = ig_account.get('id')
                ig_user = ig_account.get('username', 'Unknown')
                followers = ig_account.get('followers_count', 'N/A')
                print(f"  [OK] LINKED INSTAGRAM ACCOUNT FOUND!")
                print(f"     - Username: @{ig_user}")
                print(f"     - Account ID: {ig_id}")
                if followers != 'N/A':
                    print(f"     - Followers: {followers}")
                print(f"  [SUCCESS] The VoicePad AI pipeline can publish directly to @{ig_user}!")
            else:
                print("  [WARN] No Instagram Professional Account is linked to this Facebook Page.")
                print("     To fix:")
                print("     1. Go to Facebook Page Settings -> Linked Accounts -> Instagram.")
                print("     2. Ensure your Instagram account is switched to Creator or Business.")
                print("     3. Or explicitly configure the INSTAGRAM_ACCOUNT_ID secret.")
        else:
            print(f"  [WARN] Could not retrieve linked Instagram account ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"  [ERROR] Error querying linked Instagram account: {e}")

    # 3. Check Token Permissions
    print("\n[4] Checking Access Token Permissions...")
    try:
        debug_url = f"{GRAPH_URL}/debug_token"
        debug_resp = requests.get(debug_url, params={'input_token': page_token, 'access_token': page_token}, timeout=15)
        if debug_resp.status_code == 200:
            scopes = debug_resp.json().get('data', {}).get('scopes', [])
            print(f"  Granted Permissions: {', '.join(scopes)}")
            needed = ['pages_manage_posts', 'pages_read_engagement', 'instagram_basic', 'instagram_content_publish']
            missing = [s for s in needed if s not in scopes]
            if missing:
                print(f"  [WARN] Some recommended permissions are missing: {', '.join(missing)}")
            else:
                print("  [OK] All recommended permissions are present.")
    except Exception:
        pass

if __name__ == '__main__':
    print("=" * 60)
    print("      VOCPD - VoicePad AI Setup Diagnostics")
    print("=" * 60)
    check_ffmpeg()
    check_meta_connection()
    print("\nDiagnostic complete.")
