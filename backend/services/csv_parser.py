import pandas as pd
import io
import re
from typing import Optional

EXCLUDED_ACCOUNTS = {"603917386", "603917403"}
TRADING_ACCOUNT_NAMES = {
    "Z30350753": "Individual - TOD",
    "241942274": "Rollover IRA (241)",
    "258546864": "Rollover IRA (258)",
}
TAXABLE_ACCOUNT = "Z30350753"


def clean_currency(val) -> Optional[float]:
    if pd.isna(val):
        return None
    s = str(val).replace("$", "").replace(",", "").replace("+", "").replace("%", "").strip()
    if s in ("", "--", "N/A", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_option_symbol(symbol: str) -> Optional[dict]:
    s = symbol.strip().lstrip("-")
    m = re.match(r"^([A-Z0-9]+?)(\d{6})([CP])(\d+(?:\.\d+)?)$", s)
    if not m:
        return None
    underlying, date_str, cp, strike = m.groups()
    exp_date = f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"
    return {
        "underlying": underlying,
        "expiration": exp_date,
        "call_put": "CALL" if cp == "C" else "PUT",
        "strike": float(strike),
    }


def is_option(symbol: str) -> bool:
    if not isinstance(symbol, str):
        return False
    s = symbol.strip().lstrip("-")
    return bool(re.match(r"^[A-Z0-9]+\d{6}[CP]\d+", s))


def parse_positions(file_bytes: bytes) -> pd.DataFrame:
    content = file_bytes.decode("utf-8-sig", errors="replace")
    lines = content.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if "Account Number" in line:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not find header row in positions file")

    data_lines = []
    for line in lines[header_idx:]:
        if "Brokerage services" in line or "Date downloaded" in line:
            break
        data_lines.append(line)

    # Use index_col=False so account number col doesn't get absorbed as row index
    df = pd.read_csv(io.StringIO("\n".join(data_lines)), index_col=False)
    df.columns = df.columns.str.strip()

    # Fidelity layout: Account Number | Account Name | Symbol | Description | Quantity | ...
    # Account Number = acct ID (Z30350753 etc)
    # Account Name   = human name (Individual - TOD etc) - we don't need this
    # Symbol         = actual ticker or option symbol
    # Description    = human-readable name
    # Then the rest of the numeric columns follow

    # Rename for clarity
    col = df.columns.tolist()
    rename = {
        col[0]: "Account Number",
        col[1]: "Account Name",
        col[2]: "Symbol",
        col[3]: "Description",
        col[4]: "Quantity",
        col[5]: "Last Price",
        col[6]: "Last Price Change",
        col[7]: "Current Value",
        col[8]: "Today_GL_Dollar",
        col[9]: "Today_GL_Pct",
        col[10]: "Total_GL_Dollar",
        col[11]: "Total_GL_Pct",
        col[12]: "Pct_Of_Account",
        col[13]: "Cost Basis Total",
        col[14]: "Average Cost Basis",
    }
    df = df.rename(columns=rename)

    # Filter excluded accounts
    df["Account Number"] = df["Account Number"].astype(str).str.strip()
    df = df[df["Account Number"].isin(TRADING_ACCOUNT_NAMES.keys())]
    df = df[df["Symbol"].notna()]
    df["Symbol"] = df["Symbol"].astype(str).str.strip()
    df = df[~df["Symbol"].str.contains("SPAXX", na=False)]
    df = df[~df["Symbol"].str.upper().str.contains("HELD IN MONEY", na=False)]

    # Clean numerics
    for col_name in ["Last Price", "Current Value", "Cost Basis Total",
                     "Average Cost Basis", "Total_GL_Dollar", "Total_GL_Pct",
                     "Today_GL_Dollar", "Today_GL_Pct"]:
        if col_name in df.columns:
            df[col_name] = df[col_name].apply(clean_currency)

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")

    # Tag type
    df["is_option"] = df["Symbol"].apply(is_option)
    df["account_label"] = df["Account Number"].map(TRADING_ACCOUNT_NAMES)
    df["is_taxable"] = df["Account Number"] == TAXABLE_ACCOUNT

    # Parse option details
    opt_mask = df["is_option"]
    if opt_mask.any():
        details = df.loc[opt_mask, "Symbol"].apply(parse_option_symbol)
        df.loc[opt_mask, "underlying"] = details.apply(lambda x: x["underlying"] if x else None)
        df.loc[opt_mask, "strike"] = details.apply(lambda x: x["strike"] if x else None)
        df.loc[opt_mask, "expiration"] = details.apply(lambda x: x["expiration"] if x else None)
        df.loc[opt_mask, "call_put"] = details.apply(lambda x: x["call_put"] if x else None)

    return df.reset_index(drop=True)


def parse_history(file_bytes: bytes) -> pd.DataFrame:
    content = file_bytes.decode("utf-8-sig", errors="replace")
    lines = content.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if "Run Date" in line:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not find header row in history file")

    data_lines = []
    for line in lines[header_idx:]:
        if not line.strip():
            break
        data_lines.append(line)

    df = pd.read_csv(io.StringIO("\n".join(data_lines)), index_col=False)
    df.columns = df.columns.str.strip()
    df["Account Number"] = df["Account Number"].astype(str).str.strip()
    df = df[~df["Account Number"].isin(EXCLUDED_ACCOUNTS)]
    df["Run Date"] = pd.to_datetime(df["Run Date"], errors="coerce")
    df["Amount ($)"] = pd.to_numeric(df["Amount ($)"], errors="coerce")
    df["Price ($)"] = pd.to_numeric(df["Price ($)"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    return df.reset_index(drop=True)


def merge_history(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([existing, new], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["Run Date", "Account Number", "Action", "Symbol", "Amount ($)"],
        keep="first"
    )
    return combined.sort_values("Run Date", ascending=False).reset_index(drop=True)


def categorize_history(df: pd.DataFrame) -> dict:
    empty = pd.DataFrame(columns=df.columns if not df.empty else [])
    if df.empty:
        return {k: empty for k in ["purchases", "sales", "deposits", "withdrawals", "dividends"]}
    action = df["Action"].fillna("")
    return {
        "purchases": df[action.str.contains("YOU BOUGHT|OPENING TRANSACTION", case=False, regex=True)],
        "sales": df[action.str.contains("YOU SOLD|CLOSING TRANSACTION", case=False, regex=True)],
        "deposits": df[action.str.contains("ELECTRONIC FUNDS TRANSFER IN|DIRECT DEPOSIT|TRANSFERRED FROM|ROLLOVER|CONTRIBUTION", case=False, regex=True)],
        "withdrawals": df[action.str.contains("ELECTRONIC FUNDS TRANSFER OUT|TRANSFERRED TO|WITHDRAWAL|DISTRIBUTION", case=False, regex=True)],
        "dividends": df[action.str.contains("DIVIDEND RECEIVED", case=False, regex=True)],
    }
