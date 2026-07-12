import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.database import init_db
from src.aggregator import run_pipeline, print_digest


def run_cli(social: bool = False):
    init_db()
    print(f"Bilaspur News Agent v0.1")
    print(f"Twitter handle: {settings.twitter_handle or '(not set)'}")
    print(f"OpenCode API: {'configured' if settings.opencode_api_key else 'MISSING'}")
    print(f"YouTube API: {'configured' if settings.youtube_api_key else '(not set)'}")
    print(f"Social scrapers: {'ENABLED' if social else 'disabled'}")
    print()

    log_file = str(Path(settings.data_dir) / "pipeline.log")
    items = run_pipeline(social=social, log_file=log_file)
    print_digest(items)


def run_dashboard():
    import uvicorn
    init_db()
    from src.dashboard import app
    print("Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


def main():
    flags = set(sys.argv[1:])
    if "dashboard" in flags:
        run_dashboard()
    else:
        run_cli(social="--social" in flags or "-s" in flags)


if __name__ == "__main__":
    main()
