from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
import os

from services.csv_parser import parse_positions, parse_history
from services.history_store import append_history, load_history, get_history_as_csv, get_history_stats
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


@app.post("/api/upload/positions")
async def upload_positions(file: UploadFile = File(...)):
    """Upload a Fidelity positions CSV. Returns parsed positions immediately."""
    content = await file.read()
    try:
        df = parse_positions(content)
        return {"rows": len(df), "message": "Positions parsed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/upload/history")
async def upload_history(files: list[UploadFile] = File(...)):
    """
    Upload one or more Fidelity history CSVs.
    Merges with existing stored history, deduplicates.
    """
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
    merged = append_history(combined_new)
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
    """Download the merged history CSV."""
    csv_content = get_history_as_csv()
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=portfolio_history_merged.csv"}
    )


@app.post("/api/dashboard")
async def get_dashboard(positions_file: UploadFile = File(...)):
    """
    Main dashboard endpoint.
    Accepts a fresh positions CSV, loads stored history, fetches Yahoo data.
    Returns full dashboard payload.
    """
    positions_bytes = await positions_file.read()

    try:
        positions_df = parse_positions(positions_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Positions parse error: {e}")

    history_df = load_history()

    # Get all unique tickers to fetch from Yahoo
    # Stocks: their own symbol; Options: underlying
    stock_tickers = list(
        positions_df[~positions_df["is_option"]]["Symbol"]
        .dropna().str.strip().str.upper().unique()
    )
    option_underlyings = list(
        positions_df[positions_df["is_option"]]["underlying"]
        .dropna().str.strip().str.upper().unique()
    )
    all_tickers = list(set(stock_tickers + option_underlyings))

    # Fetch Yahoo data
    yahoo_data = get_ticker_info_batch(all_tickers)

    # Build rows
    stock_rows = build_stock_rows(positions_df, history_df, yahoo_data)
    option_rows = build_option_rows(positions_df, history_df, yahoo_data)
    account_summaries = build_account_summaries(positions_df, history_df)

    return {
        "account_summaries": account_summaries,
        "stocks_by_account": stock_rows,
        "stocks_consolidated": consolidate_stocks(stock_rows),
        "options_by_account": option_rows,
        "options_consolidated": consolidate_options(option_rows),
        "history_stats": get_history_stats(),
    }


# Serve React SPA for all non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            from fastapi.responses import HTMLResponse
            return HTMLResponse(f.read())
    return JSONResponse({"message": "API running. Frontend not built yet."})
