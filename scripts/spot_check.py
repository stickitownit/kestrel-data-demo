"""Print the 5 planted-signal checks from the marts (run after `python run.py all`).

    python scripts/spot_check.py
"""
from pathlib import Path
import duckdb

DB = Path(__file__).resolve().parents[1] / "warehouse" / "kestrel.duckdb"
con = duckdb.connect(str(DB), read_only=True)

CHECKS = {
    "1. Total net sales (expect 2,533,032,735.60)":
        "select sum(net_amount_pkr) as total_net_sales_pkr from marts.fct_sales_lines",
    "2. Slowest products in Karachi (expect HOM-001 ~0.24, JUI-001 ~0.25)":
        """select product_sku, product_name, round(seasonality_adjusted_index, 2) as idx, is_slowing
           from marts.mart_product_city_trend where city = 'Karachi'
           order by slowdown_rank_in_city limit 5""",
    "3. Below 85% three months running (expect only SP-07, Sep 2026)":
        """select salesperson_id, month_start, round(attainment, 2) as attainment
           from marts.mart_salesperson_attainment where is_below_85_three_months_running
           order by month_start desc, salesperson_id limit 10""",
    "4. Low stock (expect KD-OIL-002 at LHE-WH, ~3.7 days)":
        """select warehouse_id, product_sku, closing_qty, round(days_of_cover, 1) as days
           from marts.mart_stock_cover order by days_of_cover limit 3""",
    "5. Churned customers (expect 9, all Multan)":
        """select city, count(*) as churned from marts.mart_customer_activity
           where is_churned group by city""",
}

for title, sql in CHECKS.items():
    print(f"\n{title}")
    print(con.sql(sql))
