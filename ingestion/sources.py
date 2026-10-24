"""Extract functions: one per raw table. Each returns a pandas DataFrame of
text columns plus metadata. They do not touch the warehouse, so they can be
tested on their own."""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from .common import RAW_DIR, finalise

ERP_DIR = RAW_DIR / "erp"
INV_FILE = RAW_DIR / "inventory" / "weekly_stock_report.xlsx"
APP_DIR = RAW_DIR / "field_app"

STOCK_SHEETS = ["KHI-WH", "LHE-WH", "ISB-WH"]
STOCK_TITLE_ROWS = 3  # title rows above the header on each warehouse sheet
EXPECTED_STOCK_HEADER = ["Week Ending", "Item Code", "Item Description", "Closing Qty"]


# ---------- ERP (CSV) ----------
def _read_csv(path, loaded_at):
    # dtype=str + keep_default_na=False keeps "KD-OIL-001 " and "12,345.00"
    # exactly as exported; empty cells become NULL in finalise().
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return finalise(df, path, loaded_at)


def erp_products(loaded_at: datetime):
    return _read_csv(ERP_DIR / "products.csv", loaded_at)


def erp_customers(loaded_at: datetime):
    return _read_csv(ERP_DIR / "customers.csv", loaded_at)


def erp_sales_invoices(loaded_at: datetime):
    return _read_csv(ERP_DIR / "sales_invoices.csv", loaded_at)


def erp_sales_invoice_lines(loaded_at: datetime):
    return _read_csv(ERP_DIR / "sales_invoice_lines.csv", loaded_at)


# ---------- Inventory (Excel) ----------
def inv_stock_report(loaded_at: datetime):
    """All warehouse sheets stacked into one table, with the sheet name kept."""
    frames = []
    for sheet in STOCK_SHEETS:
        df = pd.read_excel(INV_FILE, sheet_name=sheet, skiprows=STOCK_TITLE_ROWS, dtype=object)
        if list(df.columns) != EXPECTED_STOCK_HEADER:
            raise ValueError(
                f"{INV_FILE.name}[{sheet}]: expected header {EXPECTED_STOCK_HEADER} "
                f"on row {STOCK_TITLE_ROWS + 1}, got {list(df.columns)}"
            )
        df = df.dropna(how="all")
        df = finalise(df, INV_FILE, loaded_at)
        df.insert(0, "_sheet_name", sheet)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def inv_goods_receipts(loaded_at: datetime):
    df = pd.read_excel(INV_FILE, sheet_name="Goods Receipts", dtype=object).dropna(how="all")
    df = finalise(df, INV_FILE, loaded_at)
    df.insert(0, "_sheet_name", "Goods Receipts")
    return df


# ---------- Field-sales app (JSON / JSON Lines) ----------
def _read_api_json(path, loaded_at):
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    return finalise(pd.DataFrame(payload["data"]), path, loaded_at)


def app_salespeople(loaded_at: datetime):
    return _read_api_json(APP_DIR / "salespeople.json", loaded_at)


def app_monthly_targets(loaded_at: datetime):
    return _read_api_json(APP_DIR / "monthly_targets.json", loaded_at)


def app_visits(loaded_at: datetime):
    path = APP_DIR / "visits.jsonl"
    with open(path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return finalise(pd.DataFrame(records), path, loaded_at)


# raw table name -> extract function
TABLES = {
    "erp_products": erp_products,
    "erp_customers": erp_customers,
    "erp_sales_invoices": erp_sales_invoices,
    "erp_sales_invoice_lines": erp_sales_invoice_lines,
    "inv_stock_report": inv_stock_report,
    "inv_goods_receipts": inv_goods_receipts,
    "app_salespeople": app_salespeople,
    "app_monthly_targets": app_monthly_targets,
    "app_visits": app_visits,
}
