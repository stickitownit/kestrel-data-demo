"""Export the dashboard tables from the local DuckDB warehouse to CSV for Power BI.

    python run.py powerbi        (or: python scripts/export_powerbi.py)

Writes powerbi/data/<table>.csv. The column lists below are the single source
of truth: powerbi/kestrel_model.tmdl is generated from the same SPEC, so the
Power BI model and the CSV headers always match.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "warehouse" / "kestrel.duckdb"
OUT = REPO / "powerbi" / "data"

# table -> [(column, type)]; types: text, date, int, decimal, double, bool
SPEC: dict[str, list[tuple[str, str]]] = {
    "dim_date": [
        ("date_day", "date"), ("week_start", "date"), ("month_start", "date"),
        ("year", "int"), ("month", "int"), ("day_of_month", "int"),
    ],
    "rpt_sales_overview": [
        ("invoice_line_id", "text"), ("invoice_id", "text"), ("invoice_date", "date"),
        ("invoice_month", "date"), ("doc_type", "text"), ("is_return", "bool"),
        ("city", "text"), ("warehouse_id", "text"), ("customer_id", "text"),
        ("customer_name", "text"), ("customer_type", "text"), ("salesperson_id", "text"),
        ("salesperson_name", "text"), ("product_sku", "text"), ("product_name", "text"),
        ("category", "text"), ("brand", "text"), ("is_unknown_product", "bool"),
        ("quantity", "int"), ("gross_amount_pkr", "decimal"), ("discount_amount_pkr", "decimal"),
        ("net_amount_pkr", "decimal"), ("cost_amount_pkr", "decimal"), ("returns_amount_pkr", "decimal"),
    ],
    "mart_product_city_trend": [
        ("product_city_id", "text"), ("product_sku", "text"), ("product_name", "text"),
        ("category", "text"), ("city", "text"), ("as_of_date", "date"), ("cur_start", "date"),
        ("base_start", "date"), ("units_cur", "double"), ("units_base", "double"),
        ("daily_units_cur", "double"), ("daily_units_base", "double"), ("city_change", "double"),
        ("rest_of_country_change", "double"), ("seasonality_adjusted_index", "double"),
        ("is_slowing", "bool"), ("slowdown_rank_in_city", "int"),
    ],
    "mart_salesperson_attainment": [
        ("attainment_id", "text"), ("salesperson_id", "text"), ("salesperson_name", "text"),
        ("month_start", "date"), ("is_month_to_date", "bool"), ("target_pkr", "decimal"),
        ("actual_pkr", "decimal"), ("attainment", "double"), ("attainment_to_date", "double"),
        ("visits", "int"), ("order_visits", "int"), ("visit_to_order_rate", "double"),
        ("is_below_85", "bool"), ("is_below_85_three_months_running", "bool"),
    ],
    "mart_stock_cover": [
        ("stock_cover_id", "text"), ("warehouse_id", "text"), ("product_sku", "text"),
        ("sku_original", "text"), ("product_name", "text"), ("category", "text"),
        ("snapshot_date", "date"), ("closing_qty", "int"), ("units_sold_28d", "double"),
        ("avg_units_per_day_28d", "double"), ("days_of_cover", "double"), ("is_low_stock", "bool"),
    ],
    "mart_customer_activity": [
        ("customer_id", "text"), ("customer_name", "text"), ("customer_type", "text"),
        ("city", "text"), ("salesperson_id", "text"), ("first_order_date", "date"),
        ("last_order_date", "date"), ("order_days", "int"), ("lifetime_net_pkr", "decimal"),
        ("as_of_date", "date"), ("days_since_last_order", "int"), ("is_at_risk", "bool"),
        ("is_churned", "bool"),
    ],
    "mart_data_quality": [
        ("sort_order", "int"), ("issue", "text"), ("source_system", "text"),
        ("affected_count", "int"), ("handling", "text"),
    ],
}


def main() -> None:
    import duckdb

    if not DB.exists():
        sys.exit(f"{DB} not found. Run `python run.py all` first.")
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    for table, cols in SPEC.items():
        select = ", ".join(c for c, _ in cols)
        target = (OUT / f"{table}.csv").as_posix()
        con.execute(f"copy (select {select} from marts.{table}) to '{target}' (header, delimiter ',')")
        n = con.execute(f"select count(*) from marts.{table}").fetchone()[0]
        print(f"  {table:<30} {n:>8,} rows -> powerbi/data/{table}.csv")
    total = con.execute("select sum(net_amount_pkr) from marts.rpt_sales_overview").fetchone()[0]
    print(f"Check: total net sales = Rs {total:,.2f} (answer key: Rs 2,533,032,735.60)")


if __name__ == "__main__":
    main()
