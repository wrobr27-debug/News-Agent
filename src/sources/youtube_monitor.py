import subprocess
import os
from pathlib import Path
from datetime import datetime
from src.sources.government import NewsItem
from src.config import settings

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None


CHANNELS = [
    {"name": "Bilaspur Grand News", "id": "UCsyOylo4H11EvJO2aj8ZZTQ"},
    {"name": "IBC24", "id": "UCEXw0LZRKl9J4w65JPFvT_g"},
    {"name": "News18 Chhattisgarh", "id": "UCx2Q2Id9Q0uykQAqB4be7yQ"},
    {"name": "Zee MPCG", "id": "UC_SR1NuYftrRGIkCfP4uTiQ"},
]


def transcribe_audio(audio_path: str) -> str:
    try:
        from openai import OpenAI
        if not settings.opencode_api_key:
            return ""
        # Use standard OpenAI endpoint for Whisper transcription
        client = OpenAI(
            api_key=settings.opencode_api_key,
            base_url="https://api.openai.com/v1"
        )
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return transcript.text
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        return ""


def _get_video_transcript(video_id: str) -> str:
    video_url = f"https://youtube.com/watch?v={video_id}"
    audio_dir = Path("data") / "temp_yt"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{video_id}.m4a"
    
    try:
        import sys
        cmd = [sys.executable, "-m", "yt_dlp", "-f", "ba[ext=m4a]", "-o", str(audio_path), video_url]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        
        if audio_path.exists():
            print(f"Downloaded audio for video {video_id}. Transcribing...")
            transcript = transcribe_audio(str(audio_path))
            return transcript
    except Exception as e:
        print(f"Failed to download/transcribe YT video {video_id}: {e}")
    finally:
        if audio_path.exists():
            try:
                os.remove(audio_path)
            except Exception:
                pass
    return ""


def scrape_all(api_key: str) -> list[NewsItem]:
    if not api_key or not build:
        return []

    items = []
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        for ch in CHANNELS:
            try:
                request = youtube.search().list(
                    part="snippet",
                    channelId=ch["id"],
                    order="date",
                    maxResults=5,
                )
                response = request.execute()
                for entry in response.get("items", []):
                    snippet = entry.get("snippet", {})
                    video_id = entry.get("id", {}).get("videoId", "")
                    if not video_id:
                        continue
                    
                    # Fetch dual thumbnails
                    thumbnails = snippet.get("thumbnails", {})
                    high_thumb = thumbnails.get("high", {}).get("url", "")
                    default_thumb = thumbnails.get("default", {}).get("url", "")
                    
                    # Try to transcribe video audio via Whisper
                    transcript = _get_video_transcript(video_id)
                    summary = transcript if transcript else snippet.get("description", "")[:200]
                    
                    items.append(NewsItem(
                        source=ch["name"],
                        title=snippet.get("title", ""),
                        url=f"https://youtube.com/watch?v={video_id}",
                        summary=summary,
                        published_at=snippet.get("publishedAt", "")[:10],
                        category="video",
                        image_url=high_thumb,
                        image_url_2=default_thumb,
                    ))
            except Exception:
                continue
    except Exception:
        return items

    return items
