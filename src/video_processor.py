import os
import subprocess
import hashlib
import shutil
import httpx
from pathlib import Path

def get_hash(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()

def download_image(url: str, output_dir: str = "dist/images") -> str:
    """Download an external image URL and save it locally to bypass cross-origin hotlink blocks."""
    if not url:
        return ""
    if url.startswith("images/") or url.startswith("http://localhost") or url.startswith("127.0.0.1"):
        return url
        
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    file_name = f"img_{get_hash(url)}.jpg"
    target_file = out_path / file_name
    
    # If already downloaded, return relative path
    if target_file.exists() and target_file.stat().st_size > 100:
        return f"images/{file_name}"
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=15)
        if resp.status_code == 200:
            target_file.write_bytes(resp.content)
            return f"images/{file_name}"
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        
    return ""

def extract_frames(video_path: str, output_dir: str = "dist/images", prefix: str = "frame") -> tuple[str, str]:
    """Extract featured and in-post screenshots from a video file using ffmpeg."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    img1_name = f"{prefix}_1.jpg"
    img2_name = f"{prefix}_2.jpg"
    
    img1_path = out_path / img1_name
    img2_path = out_path / img2_name
    
    # Frame 1: SS 2 seconds
    cmd1 = ["ffmpeg", "-y", "-i", video_path, "-ss", "00:00:02", "-vframes", "1", str(img1_path)]
    # Frame 2: SS 5 seconds
    cmd2 = ["ffmpeg", "-y", "-i", video_path, "-ss", "00:00:05", "-vframes", "1", str(img2_path)]
    
    try:
        subprocess.run(cmd1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
    except Exception as e:
        print(f"ffmpeg frame extraction failed/timed out: {e}")
        
    # Fallback copy if video is too short for 5s frame
    if img1_path.exists() and not img2_path.exists():
        try:
            shutil.copy(img1_path, img2_path)
        except Exception:
            pass
            
    rel_img1 = f"images/{img1_name}" if img1_path.exists() else ""
    rel_img2 = f"images/{img2_name}" if img2_path.exists() else ""
    
    return rel_img1, rel_img2
