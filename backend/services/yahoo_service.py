import json
import os
from datetime import datetime, timedelta

DATA_DIR = os.environ.get("DATA_DIR", "./data")
CACHE_FILE = os.path.join(DATA_DIR, "ticker_cache.json")
CACHE_TTL_MINUTES = 15


def _load_cache() -> dict:
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        ts = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
        if datetime.now() - ts < timedelta(minutes=CACHE_TTL_MINUTES):
            return data.get("tickers", {})
    except Exception:
        pass
    return {}


def _save_cache(tickers_data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "tickers": tickers_data}, f)
    except Exception:
        pass


def _empty_result() -> dict:
    return {"current_price": None, "next_earnings_date": None, "earnings_history": []}


def _fetch_from_yahoo(tickers: list[str]) -> dict:
    results = {t: _empty_result() for t in tickers}
    try:
        from yahooquery import Ticker
        t_obj = Ticker(tickers, timeout=20)

        # Current prices
        try:
            price_data = t_obj.price
            for ticker in tickers:
                info = price_data.get(ticker, {})
                if isinstance(info, dict):
                    price = info.get("regularMarketPrice")
                    if price is not None:
                        results[ticker]["current_price"] = round(float(price), 4)
        except Exception:
            pass

        # Next earnings dates
        try:
            calendar = t_obj.calendar_events
            for ticker in tickers:
                cal = calendar.get(ticker)
                if isinstance(cal, dict):
                    dates = cal.get("earnings", {}).get("earningsDate", [])
                    if dates:
                        results[ticker]["next_earnings_date"] = str(dates[0])[:10]
        except Exception:
            pass

        # Earnings history (last 6 quarters)
        try:
            earnings_map = t_obj.earnings
            for ticker in tickers:
                data = earnings_map.get(ticker)
                if not isinstance(data, dict):
                    continue
                quarterly = data.get("earningsChart", {}).get("quarterly", [])
                history = []
                for item in quarterly[-6:]:
                    actual = item.get("actual", {})
                    estimate = item.get("estimate", {})
                    act_val = actual.get("raw") if isinstance(actual, dict) else None
                    est_val = estimate.get("raw") if isinstance(estimate, dict) else None
                    if act_val is None or est_val is None:
                        continue
                    surprise = round((act_val - est_val) / abs(est_val) * 100, 2) if est_val else None
                    history.append({
                        "date": str(item.get("date", ""))[:10],
                        "estimated_eps": round(float(est_val), 3),
                        "actual_eps": round(float(act_val), 3),
                        "surprise_pct": surprise,
                        "beat": act_val >= est_val,
                    })
                results[ticker]["earnings_history"] = history
        except Exception:
            pass

    except Exception:
        pass

    return results


def get_ticker_info_batch(tickers: list[str]) -> dict:
    if not tickers:
        return {}

    cache = _load_cache()
    missing = [t for t in tickers if t not in cache]

    if missing:
        fresh = _fetch_from_yahoo(missing)
        cache.update(fresh)
        _save_cache(cache)

    return {t: cache.get(t, _empty_result()) for t in tickers}
