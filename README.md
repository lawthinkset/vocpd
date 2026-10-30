# VoicePad AI — vocpd

AI Voice Transcription video pipeline. Speak Naturally. AI Does the Rest.

Modelled on [chrmts](https://github.com/lawthinkset/chrmts) (`13d8a23`), rebranded for VoicePad AI.

App: [VoicePad AI on the App Store](https://apps.apple.com/nl/app/voicepad-ai/id6758025779?l=en-GB)
- AI Voice Transcription, Clean / Friendly / Professional / Summary / Movie Script tones
- High Quality Recording, AI-Powered Enhancement, Multiple Languages, Smart Summaries
- Transform your voice into polished text instantly.

## Pipeline

- `auto_pipeline.py` — validate secrets, fetch from Drive, select/process one video, publish to FB + IG
- `google_drive_fetch.py` — Drive folder `1B7tWqd5fo0ZMZOhryskEEOfkwvPvYsnB` via service-account, `Videos/`
- `process_videos.py` — ffprobe + ffmpeg 1080x1920, unsharp, libx264 CRF23, aac 128k 44.1k stereo, -t 60
- `daily_publisher.py` — Pollinations caption + VoicePad fallback captions, pinned comment with App Store link, FB video_reels + pinned comment + story, IG resumable REELS + publish + comment, `published_videos.json` dedup
- `.github/workflows/run.yml` — cron `17 4/12/20` + dispatch, py3.11 ffmpeg, `python auto_pipeline.py`, commit published list
- `check_instagram.py` — verify Page + linked IG + permissions

## Secrets (GitHub Actions)

- `FB_PAGE_ID` — numeric ID for page `voicepad ai` from `GET /me/accounts`
- `FB_PAGE_ACCESS_TOKEN` — page token for that page
- `INSTAGRAM_ACCOUNT_ID` — from `GET /{PAGE_ID}?fields=instagram_business_account`
- `GOOGLE_SERVICE_ACCOUNT_KEY` — service-account JSON
- `GOOGLE_DRIVE_FOLDER_ID` — `1B7tWqd5fo0ZMZOhryskEEOfkwvPvYsnB`
- `POLLINATIONS_API_KEY`
- `PINNED_COMMENT_LINK` — `https://apps.apple.com/nl/app/voicepad-ai/id6758025779?l=en-GB`

Pinned comment always carries the App Store link verbatim, no shortener.
