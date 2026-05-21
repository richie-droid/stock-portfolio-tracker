import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd


def get_current_price(ticker: str) -> Optional[float]:
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        return round(float(info.last_price), 4)
    except Exception:
        return None


def get_next_earnings_date(ticker: str) -> Optional[str]:
    try:
        t = yf.Ticker(ticker)
        cal = t.calendar
        if cal is None:
            return None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if ed:
                if isinstance(ed, list) and len(ed) > 0:
                    return str(ed[0])[:10]
                return str(ed)[:10]
        # DataFrame format (older yfinance)
        if hasattr(cal, "loc"):
            try:
                ed = cal.loc["Earnings Date"]
                if hasattr(ed, "iloc"):
                    return str(ed.iloc[0])[:10]
                return str(ed)[:10]
            except Exception:
                pass
        return None
    except Exception:
        return None


def get_earnings_history(ticker: str, periods: int = 6) -> list[dict]:
    """
    Returns last N quarterly earnings results.
    Each item: { date, estimated_eps, actual_eps, surprise_pct, beat }
    """
    try:
        t = yf.Ticker(ticker)
        eh = t.earnings_history
        if eh is None or eh.empty:
            return []

        eh = eh.sort_values("quarter", ascending=False).head(periods)
        results = []
        for _, row in eh.iterrows():
            estimated = row.get("epsEstimate")
            actual = row.get("epsActual")
            surprise_pct = row.get("epsDifference")

            if pd.isna(estimated) or pd.isna(actual):
                continue

            beat = float(actual) >= float(estimated)
            surprise = round(float(surprise_pct) * 100, 2) if not pd.isna(surprise_pct) else None

            results.append({
                "date": str(row.get("quarter", ""))[:10],
                "estimated_eps": round(float(estimated), 3),
                "actual_eps": round(float(actual), 3),
                "surprise_pct": surprise,
                "beat": beat,
            })
        return results
    except Exception:
        return []


def get_ticker_info_batch(tickers: list[str]) -> dict:
    """
    Fetch price, next earnings date, and earnings history for a list of tickers.
    Returns dict keyed by ticker.
    """
    results = {}
    for ticker in tickers:
        results[ticker] = {
            "current_price": get_current_price(ticker),
            "next_earnings_date": get_next_earnings_date(ticker),
            "earnings_history": get_earnings_history(ticker),
        }
    return results
