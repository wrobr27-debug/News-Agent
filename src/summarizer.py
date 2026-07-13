from datetime import datetime
from openai import OpenAI
from src.config import settings
from src.sources.government import NewsItem


def summarize_items(items: list[NewsItem]) -> list[NewsItem]:
    """Use OpenCode API to categorize and summarize news items."""
    if not settings.opencode_api_key or not items:
        for item in items:
            if not item.category or item.category == "general":
                item.category = _guess_category(item)
        return items

    client = OpenAI(
        api_key=settings.opencode_api_key,
        base_url=settings.opencode_api_base,
    )

    max_to_summarize = 30
    to_process = items[:max_to_summarize]

    batch_size = 5
    for i in range(0, len(to_process), batch_size):
        batch = to_process[i:i + batch_size]
        try:
            _process_batch(client, batch)
        except Exception:
            for item in batch:
                if not item.category or item.category == "general":
                    item.category = _guess_category(item)

    for item in items[max_to_summarize:]:
        if not item.category or item.category == "general":
            item.category = _guess_category(item)

    return items


def _process_batch(client: OpenAI, batch: list[NewsItem]):
    texts = "\n".join(
        f"{j+1}. [{item.source}] {item.title} | {item.summary[:100]}"
        for j, item in enumerate(batch)
    )

    resp = client.chat.completions.create(
        model=settings.opencode_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You categorize Bilaspur news. Return a JSON array. "
                    "Each object: category (government/police/education/business/event/news/social/infrastructure/health/railway/other), "
                    "headline (format: 'English Headline / हिंदी हेडलाइन', max 120 chars total), "
                    "importance (1-5). ONLY valid JSON."
                )
            },
            {
                "role": "user",
                "content": f"Categorize:\n{texts}"
            }
        ],
        temperature=0.1,
        max_tokens=3000,
    )

    content = resp.choices[0].message.content
    if not content:
        return

    try:
        import json, re
        content = content.strip()
        match = re.search(r'\[.*?\]', content, re.DOTALL)
        if match:
            content = match.group()
        results = json.loads(content)
        for j, result in enumerate(results):
            if j < len(batch):
                batch[j].category = result.get("category", batch[j].category)
                if result.get("headline"):
                    batch[j].title = result.get("headline")
                if not batch[j].summary:
                    batch[j].summary = result.get("headline", "")
                if result.get("importance", 0) >= 4:
                    batch[j].category = "breaking:" + batch[j].category
    except Exception:
        pass


CATEGORY_KEYWORDS = {
    "government": ["collector", "district", "administration", "cm", "chief minister", "cmo", "yojana", "scheme"],
    "police": ["police", "crime", "arrest", "traffic", "missing", "safety"],
    "education": ["school", "college", "university", "exam", "result", "admission", "student"],
    "business": ["restaurant", "cafe", "hotel", "shop", "store", "mall", "startup", "business"],
    "event": ["fest", "festival", "event", "marathon", "exhibition", "fair", "competition"],
    "health": ["hospital", "clinic", "health", "disease", "camp", "doctor"],
    "railway": ["train", "railway", "rail", "platform", "station"],
    "infrastructure": ["road", "flyover", "bridge", "construction", "pwd", "smart city", "project"],
}


def _guess_category(item: NewsItem) -> str:
    text = f"{item.title} {item.summary} {item.source}".lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return cat
    return "news"


def split_yt_transcript_into_stories(title: str, transcript: str, source: str, base_url: str) -> list[NewsItem]:
    """Split a multi-story YouTube transcript into individual NewsItems using the LLM."""
    if not settings.opencode_api_key or not transcript or len(transcript) < 150:
        # Fallback: if transcript is short or no key, return a single item with the original transcript as summary
        return [NewsItem(
            source=source,
            title=title,
            url=base_url,
            summary=transcript or title,
            category="youtube",
            published_at=datetime.now().isoformat()[:10]
        )]
        
    client = OpenAI(
        api_key=settings.opencode_api_key,
        base_url=settings.opencode_api_base,
    )
    
    try:
        resp = client.chat.completions.create(
            model=settings.opencode_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a news editor. You are given a transcript of a news broadcast containing one or more distinct news stories about Bilaspur city. "
                        "Split the transcript into a JSON array of individual news stories. If there is only one story, return a single object inside the array. "
                        "Each object must have: "
                        "category (government/police/education/business/event/news/social/infrastructure/health/railway/other), "
                        "headline (format: 'English Headline / हिंदी हेडलाइन', max 120 chars total), "
                        "summary (a detailed 2-3 sentence summary/description of the story in Hindi or English, max 200 chars), "
                        "importance (1-5). "
                        "ONLY return valid JSON. Do not include markdown code block backticks."
                    )
                },
                {
                    "role": "user",
                    "content": f"Title: {title}\nTranscript:\n{transcript}"
                }
            ],
            temperature=0.1,
            max_tokens=3000,
        )
        
        content = resp.choices[0].message.content
        if not content:
            raise ValueError("Empty response")
            
        import json, re
        content = content.strip()
        match = re.search(r'\[.*?\]', content, re.DOTALL)
        if match:
            content = match.group()
        results = json.loads(content)
        
        items = []
        for idx, result in enumerate(results):
            category = result.get("category", "youtube")
            if result.get("importance", 0) >= 4:
                category = "breaking:" + category
                
            items.append(NewsItem(
                source=source,
                title=result.get("headline", title),
                url=f"{base_url}#story{idx+1}" if len(results) > 1 else base_url,
                summary=result.get("summary", ""),
                category=category,
                published_at=datetime.now().isoformat()[:10]
            ))
        return items
    except Exception as e:
        print(f"Failed to split transcript into stories: {e}")
        return [NewsItem(
            source=source,
            title=title,
            url=base_url,
            summary=transcript or title,
            category="youtube",
            published_at=datetime.now().isoformat()[:10]
        )]
