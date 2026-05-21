import pandas as pd
from datetime import datetime
from typing import Optional
from collections import defaultdict
from services.csv_parser import TAXABLE_ACCOUNT, TRADING_ACCOUNT_NAMES, categorize_history


def get_last_purchase_date(symbol: str, account_number: str, purchases_df: pd.DataFrame) -> Optional[str]:
    if purchases_df.empty:
        return None
    mask = (
        purchases_df["Symbol"].astype(str).str.strip().str.upper() == symbol.strip().upper()
    ) & (
        purchases_df["Account Number"].astype(str) == str(account_number)
    )
    matches = purchases_df[mask]
    if matches.empty:
        return None
    latest = matches["Run Date"].max()
    return str(latest)[:10] if not pd.isna(latest) else None


def get_tax_status(symbol: str, account_number: str, purchases_df: pd.DataFrame) -> Optional[str]:
    if str(account_number) != TAXABLE_ACCOUNT:
        return None
    if purchases_df.empty:
        return None
    mask = (
        purchases_df["Symbol"].astype(str).str.strip().str.upper() == symbol.strip().upper()
    ) & (
        purchases_df["Account Number"].astype(str) == str(account_number)
    )
    matches = purchases_df[mask]
    if matches.empty:
        return None
    earliest = matches["Run Date"].min()
    if pd.isna(earliest):
        return None
    days_held = (datetime.now() - earliest).days
    return "Long Term" if days_held > 365 else "Short Term"


def build_stock_rows(positions_df: pd.DataFrame, history_df: pd.DataFrame, yahoo_data: dict) -> list[dict]:
    stocks = positions_df[~positions_df["is_option"]].copy()
    cats = categorize_history(history_df)
    purchases = cats["purchases"]
    rows = []
    for _, row in stocks.iterrows():
        symbol = str(row["Symbol"]).strip()
        acct = str(row["Account Number"]).strip()
        ydata = yahoo_data.get(symbol, {})

        live_price = ydata.get("current_price")
        csv_price = row.get("Last Price")
        current_price = live_price if live_price is not None else csv_price

        qty = row.get("Quantity") or 0
        cost_basis = row.get("Cost Basis Total") or 0

        if live_price is not None and qty:
            current_value = round(float(live_price) * float(qty), 2)
            gl_dollar = round(current_value - float(cost_basis), 2) if cost_basis else None
            gl_pct = round((gl_dollar / float(cost_basis)) * 100, 4) if cost_basis and gl_dollar is not None else None
        else:
            current_value = row.get("Current Value")
            gl_dollar = row.get("Total_GL_Dollar")
            gl_pct = row.get("Total_GL_Pct")

        rows.append({
            "symbol": symbol,
            "account_number": acct,
            "account_label": row["account_label"],
            "quantity": row.get("Quantity"),
            "avg_cost": row.get("Average Cost Basis"),
            "cost_basis_total": row.get("Cost Basis Total"),
            "current_price": current_price,
            "current_value": current_value,
            "gl_dollar": gl_dollar,
            "gl_pct": gl_pct,
            "today_gl_dollar": row.get("Today_GL_Dollar"),
            "today_gl_pct": row.get("Today_GL_Pct"),
            "last_purchase_date": get_last_purchase_date(symbol, acct, purchases),
            "tax_status": get_tax_status(symbol, acct, purchases),
            "next_earnings_date": ydata.get("next_earnings_date"),
            "earnings_history": ydata.get("earnings_history", []),
        })
    return rows


def build_option_rows(positions_df: pd.DataFrame, history_df: pd.DataFrame, yahoo_data: dict) -> list[dict]:
    options = positions_df[positions_df["is_option"]].copy()
    cats = categorize_history(history_df)
    purchases = cats["purchases"]
    rows = []
    for _, row in options.iterrows():
        symbol = str(row["Symbol"]).strip()
        acct = str(row["Account Number"]).strip()
        underlying = str(row.get("underlying") or "").strip()
        ydata = yahoo_data.get(underlying, {}) if underlying else {}
        rows.append({
            "symbol": symbol,
            "account_number": acct,
            "account_label": row["account_label"],
            "underlying": underlying,
            "strike": row.get("strike"),
            "expiration": row.get("expiration"),
            "call_put": row.get("call_put"),
            "contracts": row.get("Quantity"),
            "avg_cost": row.get("Average Cost Basis"),
            "cost_basis_total": row.get("Cost Basis Total"),
            "current_price": row.get("Last Price"),
            "current_value": row.get("Current Value"),
            "gl_dollar": row.get("Total_GL_Dollar"),
            "gl_pct": row.get("Total_GL_Pct"),
            "today_gl_dollar": row.get("Today_GL_Dollar"),
            "today_gl_pct": row.get("Today_GL_Pct"),
            "last_purchase_date": get_last_purchase_date(symbol, acct, purchases),
            "next_earnings_date": ydata.get("next_earnings_date"),
            "earnings_history": ydata.get("earnings_history", []),
        })
    return rows


def consolidate_stocks(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["symbol"]].append(r)
    consolidated = []
    for symbol, group in grouped.items():
        total_qty = sum(r["quantity"] or 0 for r in group)
        total_cost = sum(r["cost_basis_total"] or 0 for r in group)
        total_value = sum(r["current_value"] or 0 for r in group)
        total_gl = sum(r["gl_dollar"] or 0 for r in group)
        avg_cost = total_cost / total_qty if total_qty else None
        gl_pct = (total_gl / total_cost * 100) if total_cost else None
        latest_purchase = max(
            (r["last_purchase_date"] for r in group if r["last_purchase_date"]),
            default=None
        )
        base = group[0]
        consolidated.append({
            **base,
            "account_number": "ALL",
            "account_label": "All Accounts",
            "quantity": total_qty,
            "avg_cost": avg_cost,
            "cost_basis_total": total_cost,
            "current_value": total_value,
            "gl_dollar": total_gl,
            "gl_pct": gl_pct,
            "last_purchase_date": latest_purchase,
            "tax_status": None,
        })
    return consolidated


def consolidate_options(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for r in rows:
        key = (r["underlying"], r["strike"], r["expiration"])
        grouped[key].append(r)
    consolidated = []
    for (underlying, strike, expiration), group in grouped.items():
        total_contracts = sum(r["contracts"] or 0 for r in group)
        total_cost = sum(r["cost_basis_total"] or 0 for r in group)
        total_value = sum(r["current_value"] or 0 for r in group)
        total_gl = sum(r["gl_dollar"] or 0 for r in group)
        avg_cost = total_cost / total_contracts if total_contracts else None
        gl_pct = (total_gl / total_cost * 100) if total_cost else None
        latest_purchase = max(
            (r["last_purchase_date"] for r in group if r["last_purchase_date"]),
            default=None
        )
        base = group[0]
        consolidated.append({
            **base,
            "account_number": "ALL",
            "account_label": "All Accounts",
            "contracts": total_contracts,
            "avg_cost": avg_cost,
            "cost_basis_total": total_cost,
            "current_value": total_value,
            "gl_dollar": total_gl,
            "gl_pct": gl_pct,
            "last_purchase_date": latest_purchase,
        })
    return consolidated


def build_account_summaries(
    positions_df: pd.DataFrame,
    history_df: pd.DataFrame,
    live_rows: list[dict] | None = None,
) -> list[dict]:
    cats = categorize_history(history_df)
    summaries = []
    account_keys = list(TRADING_ACCOUNT_NAMES.keys()) + ["TOTAL"]

    for acct in account_keys:
        if acct == "TOTAL":
            pos = positions_df
            deposits = cats["deposits"]
            withdrawals = cats["withdrawals"]
            sales = cats["sales"]
            dividends = cats["dividends"]
            acct_live = live_rows or []
        else:
            pos = positions_df[positions_df["Account Number"].astype(str) == acct]
            def _filter(df):
                if df.empty:
                    return pd.DataFrame()
                return df[df["Account Number"].astype(str) == acct]
            deposits = _filter(cats["deposits"])
            withdrawals = _filter(cats["withdrawals"])
            sales = _filter(cats["sales"])
            dividends = _filter(cats["dividends"])
            acct_live = [r for r in (live_rows or []) if r.get("account_number") == acct]

        # Prefer live rows for current values; fall back to CSV
        if acct_live:
            current_value = sum(r.get("current_value") or 0 for r in acct_live)
            unrealized_gl = sum(r.get("gl_dollar") or 0 for r in acct_live)
        else:
            current_value = pos["Current Value"].sum() if "Current Value" in pos.columns and not pos.empty else 0
            unrealized_gl = pos["Total_GL_Dollar"].sum() if "Total_GL_Dollar" in pos.columns and not pos.empty else 0

        fresh_funds = deposits["Amount ($)"].sum() if not deposits.empty else 0
        cash_out = abs(withdrawals["Amount ($)"].sum()) if not withdrawals.empty else 0
        realized = sales["Amount ($)"].sum() if not sales.empty else 0
        dividends_total = dividends["Amount ($)"].sum() if not dividends.empty else 0

        summaries.append({
            "account_number": acct,
            "account_label": TRADING_ACCOUNT_NAMES.get(acct, "Total"),
            "current_value": round(float(current_value), 2),
            "unrealized_gl": round(float(unrealized_gl), 2),
            "fresh_funds_invested": round(float(fresh_funds), 2),
            "cash_taken_out": round(float(cash_out), 2),
            "realized_gains": round(float(realized), 2),
            "dividends_received": round(float(dividends_total), 2),
        })

    return summaries
