import os
import sys
import json
import random
import re
import urllib.parse
import requests
from upload.upload_facebook import upload_reel, upload_story
from upload.upload_instagram import upload_reel as ig_reel, get_connected_instagram_account

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PUBLISHED_FILE = 'published_videos.json'

def load_published():
    if os.path.exists(PUBLISHED_FILE):
        try:
            with open(PUBLISHED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_published(data):
    with open(PUBLISHED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def extract_subject_from_filename(filename):
    """
    Extracts descriptive keywords from video filename.
    """
    name = os.path.splitext(filename)[0]
    name = re.sub(r'_\d{8,}', '', name)
    name = re.sub(r'\d+', '', name)
    name = name.replace('_', ' ').replace('-', ' ').strip()
    return name or "AI voice transcription with Smart Summaries"

def clean_caption(text, subject="voice transcription"):
    if not text:
        return None
    # 1. Remove think tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 2. Filter reasoning / meta lines
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        l = line.strip()
        if re.search(r'^(role\s*:?\s*assistant|reasoning\s*:|thought\s*:|thinking\s*:)', l, re.IGNORECASE):
            continue
        if re.search(r'^(here\s+is|here\'s|as\s+requested|certainly|sure,|note:|\*using\s+key|\*this\s+caption|---)', l, re.IGNORECASE):
            continue
        filtered_lines.append(line)
    text = '\n'.join(filtered_lines)
    # 3. Remove Title / Description / Caption / Hashtags labels
    text = re.sub(r'\*\*(title|description|caption|hashtags)[^\*]*\*\*[:\s]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^(title|description|caption|hashtags)\s*:\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
    # 4. Remove Pollinations ads / footers
    text = re.sub(r'(Support\s+Pollinations|Powered\s+by\s+Pollinations|🌸\s*Ad\s*🌸).*$', '', text, flags=re.IGNORECASE | re.DOTALL).strip()
    # 5. Remove quotes, asterisks, and normalize spaces
    text = text.replace('"', '').replace('“', '').replace('”', '').replace('*', '').strip()
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. Blacklist check - if ANY meta/reasoning words remain, reject
    blacklist = [
        'role assistant', 'assistant reasoning', 'reasoning', '<think>',
        'we must produce', 'here is a', 'title:', 'description:',
        'seo optimized', 'social media post', 'char)'
    ]
    lower_text = text.lower()
    for bad in blacklist:
        if bad in lower_text:
            return None

    if len(text) < 25:
        return None

    if len(text) > 280:
        text = text[:280].rsplit(' ', 1)[0]

    return text

def generate_caption(filename=""):
    pollinations_key = os.environ.get('POLLINATIONS_API_KEY', '').strip()
    subject = extract_subject_from_filename(filename) if filename else "AI voice transcription note"

    if not pollinations_key:
        return get_fallback_caption(subject)

    system_prompt = (
        "You are an expert productivity and tech copywriter and viral marketer for VoicePad AI "
        "(https://apps.apple.com/nl/app/voicepad-ai/id6758025779?l=en-GB), "
        "an AI voice transcription app for iPhone. VoicePad AI - AI Voice Transcription. Speak Naturally. AI Does the Rest. "
        "VoicePad AI transforms voice into polished text instantly with Clean, Friendly, Professional, Summary and Movie Script tones, "
        "smart transcript cleaning, multi-language support (EN/ES/FR/DE/PT+), offline high quality recording, "
        "organized library, and export/share. "
        "OUTPUT ONLY the final single-line caption with hashtags. "
        "NEVER output your thoughts, NEVER output reasoning, NEVER output role tags, "
        "and NEVER use labels like Title: or Description:. "
        "Start immediately with an emoji and a compelling hook."
    )
    user_prompt = (
        f"Write a viral, compelling Instagram and Facebook Reel caption about {subject} — "
        f"highlighting how VoicePad AI lets anyone speak naturally and get perfect notes instantly with AI enhancement, "
        f"multiple languages, and smart summaries in Clean, Professional, Summary or Movie Script tone. "
        f"Include popular hashtags (#VoicePadAI #VoiceToText #AITranscription #Productivity #NoteTaking #StudyHacks #MeetingNotes #iPhoneApp). "
        f"Keep it punchy, engaging, and under 220 characters."
    )

    try:
        url = "https://gen.pollinations.ai/v1/chat/completions"
        payload = {
            'model': 'google/gemini-2.5-flash-lite',
            'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
            'max_tokens': 220, 'temperature': 0.9
        }
        headers = {'Authorization': f'Bearer {pollinations_key}', 'Content-Type': 'application/json'}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            text = resp.json().get('choices', [{}])[0].get('message', {}).get('content', ''); cleaned = clean_caption(text, subject)
            if cleaned:
                return cleaned
            else:
                print(f"  [WARN] Pollinations response contained meta/reasoning or failed validation. Using fallback.")
    except Exception as e:
        print(f"  [WARN] Pollinations caption generation failed: {e}")

    return get_fallback_caption(subject)

def get_fallback_caption(subject="voice notes"):
    captions = [
        "🎨 Speak naturally & get perfect notes instantly with VoicePad AI! 🎙️✨ #VoicePadAI #VoiceToText #AITranscription #Productivity #NoteTaking",
        "✨ Turn rambling voice into Clean, Professional or Summary text in one tap with VoicePad AI 🎯 #VoicePadAI #SmartSummaries #MeetingNotes #StudyHacks",
        "👁️ High Quality Recording + AI Enhancement! Filler removed, grammar fixed automatically 🎧 #VoicePadAI #HighQualityRecording #AIEnhancement #iPhoneApp",
        "🚀 From lecture to Summary to Movie Script mode in seconds! VoicePad AI does the rest 🎬 #VoicePadAI #MovieScript #Summary #MultipleLanguages",
        "📸 Tap mic, speak, pick a tone and export! VoicePad AI works offline anywhere 🎙️📝 #VoicePadAI #VoiceRecording #Productivity #NoteTaking",
        "🎯 Multiple Languages EN/ES/FR/DE/PT+! Your global voice companion 🌍🎧 #VoicePadAI #MultipleLanguages #AITranscription #iPhoneApp",
        "💡 Stop retyping recordings! AI cleans transcripts and structures notes instantly 📲🔥 #VoicePadAI #SmartSummaries #Productivity #MeetingNotes",
        "🌟 Speak Naturally. AI Does the Rest. Try VoicePad AI free on the App Store 🎨⚡ #VoicePadAI #AIvoiceTranscription #NoteTaking #Productivity"
    ]
    return random.choice(captions)

def generate_pinned_comment(caption=""):
    """
    Creates a dedicated high-converting pinned comment with product details and link to VoicePad AI on the App Store.
    """
    default_link = 'https://apps.apple.com/nl/app/voicepad-ai/id6758025779?l=en-GB'
    link = os.environ.get('PINNED_COMMENT_LINK', default_link).strip() or default_link
    custom_text = os.environ.get('PINNED_COMMENT_TEXT', '').strip()
    if custom_text:
        return f"{custom_text}\n\n👉 {link}"

    pinned_options = [
        (
            f"🎙️ Speak Naturally. AI Does the Rest!\n\n"
            f"VoicePad AI is your AI voice transcription app for iPhone that:\n"
            f"✅ Records in high quality even offline\n"
            f"✅ Transcribes voice to polished text instantly\n"
            f"✅ Applies Clean, Friendly, Professional, Summary & Movie Script tones\n"
            f"✅ Cleans filler, fixes grammar and structures notes\n"
            f"✅ Supports EN/ES/FR/DE/PT+ and export/share\n\n"
            f"👉 Download VoicePad AI on the App Store: {link}"
        ),
        (
            f"🚀 Turn voice into perfect notes in seconds!\n\n"
            f"VoicePad AI turns rambling recordings into clean notes, summaries or movie scripts with AI enhancement and smart transcript cleaning.\n\n"
            f"👉 Get VoicePad AI on the App Store: {link}"
        ),
        (
            f"💡 Stop retyping recordings and missing key points.\n\n"
            f"With VoicePad AI, tap mic, speak naturally, pick Clean, Professional, Summary or Movie Script tone and export/share.\n\n"
            f"👉 Try VoicePad AI free here: {link}"
        ),
        (
            f"✨ High Quality Recording, AI Enhancement, Multiple Languages, Smart Summaries!\n\n"
            f"Speak Naturally. AI Does the Rest. Which tone should I demo next: Clean / Professional / Summary / Movie Script?\n\n"
            f"👉 Download on iOS: {link}"
        )
    ]
    chosen = random.choice(pinned_options)
    if link not in chosen:
        chosen = f"{chosen}\n\n👉 Download VoicePad AI on the App Store: {link}"
    return chosen

def select_video(video_list, published):
    published_names = {p.get('filename') for p in published}
    unpublished = [v for v in video_list if os.path.basename(v) not in published_names]

    if unpublished:
        return random.choice(unpublished)

    # All published - weighted random from ALL videos
    if video_list:
        counts = {}
        for p in published:
            name = p.get('filename', '')
            counts[name] = counts.get(name, 0) + 1

        weights = []
        for v in video_list:
            name = os.path.basename(v)
            count = counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        chosen = random.choices(video_list, weights=weights, k=1)[0]
        return chosen

    return None

def resolve_target_pages():
    """
    Resolves Facebook target pages and page access tokens.
    Supports:
    1. FB_PAGE_TOKENS_JSON (pre-stored dictionary mapping page_id -> {name, token})
    2. FB_PAGE_ID + FB_PAGE_ACCESS_TOKEN (primary mode for VoicePad AI)
    """
    tokens_json_env = os.environ.get('FB_PAGE_TOKENS_JSON', '').strip()
    if tokens_json_env:
        try:
            tokens_data = json.loads(tokens_json_env)
            page_configs = []
            for pid, info in tokens_data.items():
                if isinstance(info, dict):
                    page_configs.append({
                        'id': str(pid),
                        'name': info.get('name', f'Page {pid}'),
                        'token': info.get('token')
                    })
                elif isinstance(info, str):
                    page_configs.append({
                        'id': str(pid),
                        'name': f'Page {pid}',
                        'token': info
                    })
            if page_configs:
                return page_configs
        except Exception as e:
            print(f"[WARN] Failed to parse FB_PAGE_TOKENS_JSON: {e}")

    # Primary single page mode
    single_page_id = os.environ.get('FB_PAGE_ID', '').strip()
    single_page_token = os.environ.get('FB_PAGE_ACCESS_TOKEN', '').strip()

    if single_page_id and single_page_token:
        return [{
            'id': single_page_id,
            'name': "VoicePad AI",
            'token': single_page_token
        }]

    return []

def publish_to_facebook_pages(video_path, caption, pinned_comment, page_configs):
    """
    Publishes the Reel, Pinned Comment, and Story to all configured Facebook pages.
    """
    results = []
    print(f"\n[FB] Publishing to {len(page_configs)} Facebook Page(s)...")

    for p in page_configs:
        pid = p['id']
        pname = p.get('name', pid)
        token = p['token']
        print(f"\n--- Publishing to Facebook Page: {pname} (ID: {pid}) ---")

        # 1. Reel + Pinned Comment
        reel_res = upload_reel(
            video_path=video_path,
            caption=caption,
            page_id=pid,
            page_token=token,
            pin_comment=True,
            comment_text=pinned_comment
        )
        reel_res['page_name'] = pname
        results.append(reel_res)

        # 2. Story
        story_res = upload_story(
            video_path=video_path,
            page_id=pid,
            page_token=token
        )
        story_res['page_name'] = pname
        results.append(story_res)

    return results

def publish(video_path, publish_to_facebook=True, publish_to_instagram=True):
    filename = os.path.basename(video_path)
    caption = generate_caption(filename)
    pinned_comment = generate_pinned_comment(caption)

    print(f"\n[SEO CAPTION] {caption}")
    print(f"[PINNED COMMENT] {pinned_comment}")

    results = []
    pages = []
    if publish_to_facebook or publish_to_instagram:
        pages = resolve_target_pages()

    if publish_to_facebook:
        if not pages:
            print("[WARN] No target Facebook pages resolved. Please configure FB_PAGE_ID + FB_PAGE_ACCESS_TOKEN.")
        else:
            fb_results = publish_to_facebook_pages(video_path, caption, pinned_comment, pages)
            results.extend(fb_results)

    if publish_to_instagram:
        ig_account_id = os.environ.get('INSTAGRAM_ACCOUNT_ID', '').strip()
        single_page_token = os.environ.get('FB_PAGE_ACCESS_TOKEN', '').strip()
        first_page_id = None

        if pages:
            if not single_page_token:
                single_page_token = pages[0].get('token', '')
            first_page_id = pages[0].get('id', '')
        else:
            first_page_id = os.environ.get('FB_PAGE_ID', '').strip()

        # Auto-detect linked Instagram Business/Creator account if not explicitly set
        if not ig_account_id and first_page_id and single_page_token:
            auto_id, auto_username = get_connected_instagram_account(first_page_id, single_page_token)
            if auto_id:
                ig_account_id = str(auto_id)
                print(f"\n[IG AUTO-DETECT] Found linked Instagram Account: @{auto_username} (ID: {ig_account_id}) on Facebook Page {first_page_id}")

        if ig_account_id and single_page_token:
            share_to_feed = os.environ.get('IG_SHARE_TO_FEED', 'true').lower() in ('1', 'true', 'yes')
            print(f"\n[IG] Publishing Reel to Instagram Account: {ig_account_id} (share_to_feed={share_to_feed})")
            ig_res = ig_reel(
                video_path=video_path,
                caption=caption,
                page_token=single_page_token,
                ig_account_id=ig_account_id,
                share_to_feed=share_to_feed,
                comment_text=pinned_comment
            )
            results.append(ig_res)
        elif not ig_account_id:
            print("\n[INFO] Instagram publishing skipped: No Instagram Professional Account linked to Facebook Page.")
            print("  How to connect:")
            print("  1. In Meta Business Suite -> Settings -> Business Assets, link your Instagram Professional account to your Facebook Page.")
            print("  2. Or set INSTAGRAM_ACCOUNT_ID secret in GitHub repository settings.")
        elif not single_page_token:
            print("\n[SKIP] Facebook Page access token not found for Instagram.")

    return results

def run_daily_publish(processed_videos):
    published = load_published()
    video = select_video(processed_videos, published)

    if not video:
        print("[INFO] No videos available to publish")
        return []

    filename = os.path.basename(video)
    print(f"\n[SELECTED VIDEO] {filename}")

    results = publish(video, publish_to_facebook=True, publish_to_instagram=True)

    entry = {
        'filename': filename,
        'results': results
    }
    published.append(entry)
    save_published(published)

    return results

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    import glob
    processed = glob.glob('Processed_Videos/*.mp4') + glob.glob('Processed_Videos/*.mov')
    results = run_daily_publish(processed)
    print(f"\nPublish results total: {len(results)}")
