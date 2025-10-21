from pathlib import Path

# Directory paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_PATH = BASE_DIR / "data" / "app.db"

# Maximum upload size in bytes (5 MB)
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Contest definitions
CONTESTS = {
    "costumes": {
        "slug": "costumes",
        "name": "Costume Throwdown",
        "tagline": "Turn up in your wildest Halloween fits and battle for the crown.",
        "nav_label": "Costume Contest",
        "upload_title": "Upload Your Costume",
        "vote_title": "Vote for Costumes",
        "results_title": "Costume Results",
        "categories": [
            {"id": "best_costume", "label": "Best Costume"},
            {"id": "spookiest", "label": "Spookiest Costume"},
            {"id": "funniest", "label": "Funniest Costume"},
            {"id": "best_group", "label": "Best Group Costume"},
            {"id": "best_diy", "label": "Top DIY Costume"},
        ],
    },
    "pumpkins": {
        "slug": "pumpkins",
        "name": "The Great Pumpkin-Off",
        "tagline": (
            "Our mini pumpkin painting extravaganza is in full swing—pick the gourds that wowed you."
        ),
        "nav_label": "Pumpkin-Off",
        "upload_title": "Upload Your Pumpkin",
        "vote_title": "Vote for Pumpkins",
        "results_title": "Pumpkin Results",
        "categories": [
            {"id": "pumpkin_mad_genius", "label": "Mad Pumpkin Genius – Most Unique"},
            {"id": "pumpkin_picasso", "label": "Pumpkin Picasso – Most Creative"},
            {"id": "pumpkin_joker", "label": "Chief Pumpkin Joker – Funniest Pumpkin"},
            {"id": "pumpkin_cute", "label": "Adorable Gourd – Cutest Pumpkin"},
            {"id": "pumpkin_spook", "label": "Scare-tacular Pumpkin – Spookiest Pumpkin"},
            {"id": "pumpkin_spirit", "label": "Spirit of Halloween – Best Halloween Spirit"},
        ],
    },
}

DEFAULT_CONTEST = "costumes"


def ensure_directories() -> None:
    """Ensure runtime directories exist."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_contest(slug: str) -> dict:
    contest = CONTESTS.get(slug)
    if contest is None:
        raise KeyError(f"Unknown contest '{slug}'")
    return contest


def contest_category_ids(slug: str) -> set[str]:
    contest = get_contest(slug)
    return {category["id"] for category in contest["categories"]}


def all_category_ids() -> set[str]:
    ids: set[str] = set()
    for contest in CONTESTS.values():
        ids.update(category["id"] for category in contest["categories"])
    return ids


def all_contests() -> list[dict]:
    return list(CONTESTS.values())
