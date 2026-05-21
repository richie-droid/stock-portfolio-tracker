import os
from datetime import datetime

DATA_DIR = os.environ.get("DATA_DIR", "./data")
POSITIONS_FILE = os.path.join(DATA_DIR, "positions_latest.csv")
POSITIONS_META_FILE = os.path.join(DATA_DIR, "positions_meta.txt")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_positions(file_bytes: bytes):
    ensure_data_dir()
    with open(POSITIONS_FILE, "wb") as f:
        f.write(file_bytes)
    with open(POSITIONS_META_FILE, "w") as f:
        f.write(datetime.now().isoformat())


def load_positions() -> bytes | None:
    if not os.path.exists(POSITIONS_FILE):
        return None
    with open(POSITIONS_FILE, "rb") as f:
        return f.read()


def get_positions_date() -> str | None:
    try:
        with open(POSITIONS_META_FILE) as f:
            return f.read().strip()[:10]
    except Exception:
        return None


def has_positions() -> bool:
    return os.path.exists(POSITIONS_FILE)
