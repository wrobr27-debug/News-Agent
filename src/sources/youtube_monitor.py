from datetime import datetime
from src.sources.government import NewsItem

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
                    items.append(NewsItem(
                        source=ch["name"],
                        title=snippet.get("title", ""),
                        url=f"https://youtube.com/watch?v={video_id}",
                        summary=snippet.get("description", "")[:200],
                        published_at=snippet.get("publishedAt", "")[:10],
                        category="video",
                    ))
            except Exception:
                continue
    except Exception:
        return items

    return items
