from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
import os

from services.csv_parser import parse_positions, parse_history
from services.history_store import append_history, load_history, get_history_as_csv, get_history_stats
from services.positions_store import save_positions, load_positions, has_positions, get_positions_date
from services.yahoo_service import get_ticker_info_batch
from services.portfolio_service import (
    build_stock_rows,
    build_option_rows,
    consolidate_stocks,
    consolidate_options,
    build_account_summaries,
)

app = FastAPI(title="Portfolio Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React build if it exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _build_dashboard_payload(positions_bytes: bytes) -> dict:
    """Shared logic for GET and POST dashboard endpoints."""
    positions_df = parse_positions(positions_bytes)
    history_df = load_history()

    stock_tickers = list(
        positions_df[~positions_df["is_option"]]["Symbol"]
        .dropna().str.strip().str.upper().unique()
    )
    option_underlyings = list(
        positions_df[positions_df["is_option"]]["underlying"]
        .dropna().str.strip().str.upper().unique()
    )
    all_tickers = list(set(stock_tickers + option_underlyings))

    yahoo_data = get_ticker_info_batch(all_tickers)

    stock_rows = build_stock_rows(positions_df, history_df, yahoo_data)
    option_rows = build_option_rows(positions_df, history_df, yahoo_data)
    account_summaries = build_account_summaries(positions_df, history_df, stock_rows + option_rows)

    return {
        "positions_date": get_positions_date(),
        "account_summaries": account_summaries,
        "stocks_by_account": stock_rows,
        "stocks_consolidated": consolidate_stocks(stock_rows),
        "options_by_account": option_rows,
        "options_consolidated": consolidate_options(option_rows),
        "history_stats": get_history_stats(),
    }


@app.get("/api/dashboard")
def get_dashboard():
    """Load dashboard from stored positions (no upload required)."""
    if not has_positions():
        return Response(status_code=204)
    positions_bytes = load_positions()
    try:
        return _build_dashboard_payload(positions_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dashboard")
async def post_dashboard(positions_file: UploadFile = File(...)):
    """Upload a fresh positions CSV, store it, and return the dashboard."""
    positions_bytes = await positions_file.read()
    try:
        parse_positions(positions_bytes)  # validate before saving
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Positions parse error: {e}")

    save_positions(positions_bytes)

    try:
        return _build_dashboard_payload(positions_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/history")
async def upload_history(files: list[UploadFile] = File(...)):
    all_new = []
    for f in files:
        content = await f.read()
        try:
            df = parse_history(content)
            all_new.append(df)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing {f.filename}: {e}")

    if not all_new:
        raise HTTPException(status_code=400, detail="No valid history files provided")

    combined_new = pd.concat(all_new, ignore_index=True)
    append_history(combined_new)
    stats = get_history_stats()

    return {
        "message": f"History updated. {stats['rows']} total transactions stored.",
        "stats": stats,
    }


@app.get("/api/history/stats")
def history_stats():
    return get_history_stats()


@app.get("/api/history/export")
def export_history():
    csv_content = get_history_as_csv()
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=portfolio_history_merged.csv"}
    )


# Serve React SPA for all non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            from fastapi.responses import HTMLResponse
            return HTMLResponse(f.read())
    return JSONResponse({"message": "API running. Frontend not built yet."})
