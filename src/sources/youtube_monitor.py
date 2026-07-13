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


def process_video_and_transcribe(video_id: str) -> dict:
    from src.video_processor import extract_frames
    import sys
    
    video_url = f"https://youtube.com/watch?v={video_id}"
    temp_dir = Path("data") / "temp_yt"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    video_path = temp_dir / f"{video_id}.mp4"
    audio_path = temp_dir / f"{video_id}.m4a"
    
    result = {"transcript": "", "image_url": "", "image_url_2": ""}
    
    try:
        # Download worst video stream (lightweight/any format)
        cmd_dl = [sys.executable, "-m", "yt_dlp", "-f", "worst", "-o", str(video_path), video_url]
        res_dl = subprocess.run(cmd_dl, capture_output=True, text=True, timeout=75)
        if res_dl.returncode != 0:
            print(f"yt-dlp failed for video {video_id}. Stderr: {res_dl.stderr}")
            raise subprocess.CalledProcessError(res_dl.returncode, cmd_dl, output=res_dl.stdout, stderr=res_dl.stderr)
        
        if video_path.exists():
            # 1. Extract screenshots at 2s and 5s
            img1, img2 = extract_frames(str(video_path), prefix=f"yt_{video_id}")
            result["image_url"] = img1
            result["image_url_2"] = img2
            
            # 2. Extract audio from video via ffmpeg
            cmd_audio = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "copy", str(audio_path)]
            subprocess.run(cmd_audio, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            
            if audio_path.exists():
                print(f"Transcribing audio for YouTube video {video_id}...")
                transcript = transcribe_audio(str(audio_path))
                result["transcript"] = transcript
    except Exception as e:
        print(f"Failed to process YouTube video {video_id}: {e}")
    finally:
        if video_path.exists():
            try:
                os.remove(video_path)
            except Exception:
                pass
        if audio_path.exists():
            try:
                os.remove(audio_path)
            except Exception:
                pass
                
    return result


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
                    
                    # Fetch dual thumbnails (external URLs)
                    thumbnails = snippet.get("thumbnails", {})
                    high_thumb = thumbnails.get("high", {}).get("url", "")
                    default_thumb = thumbnails.get("default", {}).get("url", "")
                    
                    # Download video, extract screenshots, and transcribe spoken audio
                    res = process_video_and_transcribe(video_id)
                    
                    # Save images locally to prevent broken references / cross-origin hotlink blocks
                    from src.video_processor import download_image
                    from src.summarizer import split_yt_transcript_into_stories
                    
                    img_url = res["image_url"] if res["image_url"] else download_image(high_thumb)
                    img_url_2 = res["image_url_2"] if res["image_url_2"] else download_image(default_thumb)
                    
                    # Split transcript into multiple NewsItems if it contains multiple news stories
                    video_url = f"https://youtube.com/watch?v={video_id}"
                    split_items = split_yt_transcript_into_stories(
                        title=snippet.get("title", ""),
                        transcript=res["transcript"] if res["transcript"] else snippet.get("description", ""),
                        source=ch["name"],
                        base_url=video_url
                    )
                    
                    # Assign local image paths to all split news stories
                    for split_item in split_items:
                        split_item.image_url = img_url
                        split_item.image_url_2 = img_url_2
                        items.append(split_item)
            except Exception as e:
                print(f"Error processing YouTube video entry: {e}")
                import traceback
                traceback.print_exc()
                continue
    except Exception as e:
        print(f"YouTube scraper outer failure: {e}")
        import traceback
        traceback.print_exc()
        return items

    return items
