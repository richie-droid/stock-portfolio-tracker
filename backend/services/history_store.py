import pandas as pd
import os
from services.csv_parser import merge_history

DATA_DIR = os.environ.get("DATA_DIR", "./data")
HISTORY_FILE = os.path.join(DATA_DIR, "history_merged.csv")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_history() -> pd.DataFrame:
    ensure_data_dir()
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame()
    df = pd.read_csv(HISTORY_FILE)
    df["Run Date"] = pd.to_datetime(df["Run Date"], errors="coerce")
    return df


def save_history(df: pd.DataFrame):
    ensure_data_dir()
    df.to_csv(HISTORY_FILE, index=False)


def append_history(new_df: pd.DataFrame) -> pd.DataFrame:
    existing = load_history()
    if existing.empty:
        merged = new_df
    else:
        merged = merge_history(existing, new_df)
    save_history(merged)
    return merged


def get_history_as_csv() -> str:
    df = load_history()
    return df.to_csv(index=False)


def get_history_stats() -> dict:
    df = load_history()
    if df.empty:
        return {"rows": 0, "earliest_date": None, "latest_date": None}
    return {
        "rows": len(df),
        "earliest_date": str(df["Run Date"].min())[:10],
        "latest_date": str(df["Run Date"].max())[:10],
    }
