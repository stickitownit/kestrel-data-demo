# Sample data: Kestrel Distributors (fictional)

> **Illustrative data.** The company, brands, shops, people and numbers are all made up.
> Regenerate it at any time with `python scripts/generate_sample_data.py` (seeded, so the output is identical every run).

Period: 1 Jul 2025 – 23 Oct 2026. Currency: PKR. Data-quality issues are planted on purpose (see `docs/SPEC.md` §3). Their exact counts and the expected business answers are in `answer_key.json`.

## 1. ERP: `raw/erp/` (CSV)

**products.csv** (34 rows): `sku`, `product_name`, `category`, `brand`, `pack_size`, `unit_price_pkr` (price to the trade), `unit_cost_pkr`, `units_per_carton`, `is_active`

**customers.csv** (366 rows):
- `customer_id`, `customer_name`
- `customer_type`: Retailer / Wholesaler / Modern Trade
- `city` (messy spellings), `area`
- `salesperson_id` (sometimes blank)
- `credit_days`
- `created_on` (DD/MM/YYYY)

**sales_invoices.csv** (one row per invoice or return):
- `invoice_id` (`INV-…` or `RET-…`)
- `invoice_date` (DD/MM/YYYY)
- `customer_id`, `salesperson_id`
- `doc_type`: INV / RET
- `total_amount_pkr`: text with thousand separators. Wrong on 80 invoices; trust the lines instead.

**sales_invoice_lines.csv**:
- `invoice_id`, `line_no`
- `sku`: some lower case or with a trailing space; KD-SNK-099 is missing from the product master
- `quantity`: units, negative on returns
- `unit_price_pkr`, `discount_pct`
- Contains 406 exact duplicate rows
- Net amount = `quantity × unit_price_pkr × (1 − discount_pct)`

## 2. Inventory: `raw/inventory/weekly_stock_report.xlsx`

- **Sheets `KHI-WH`, `LHE-WH`, `ISB-WH`:**
  - 3 title rows, with the header on row 4
  - Columns: `Week Ending` (Sunday), `Item Code`, `Item Description`, `Closing Qty`
  - ISB-WH writes codes without dashes (`KDOIL001`)
- **Sheet `Goods Receipts`:** `GRN No`, `Receipt Date`, `Warehouse`, `Item Code`, `Qty Received`, `Supplier`

Warehouse coverage:
- KHI-WH: Karachi, Hyderabad
- LHE-WH: Lahore, Faisalabad, Multan
- ISB-WH: Islamabad, Rawalpindi, Peshawar

## 3. Field-sales app: `raw/field_app/` (JSON)

- **salespeople.json:** `{"data": [...]}` with `salesperson_id`, `name`, `city`, `joined_on`
- **monthly_targets.json:** `{"data": [...]}` with `salesperson_id`, `month` (YYYY-MM), `target_pkr`
- **visits.jsonl:** one JSON object per line
  - `visit_id` (127 duplicates)
  - `salesperson_id`, `customer_id`
  - `visited_at_utc` (ISO 8601, UTC; Pakistan time is UTC+5)
  - `outcome`: order / no_order / shop_closed / owner_absent
  - `order_ref`: the invoice ID when an order was taken

## 4. `answer_key.json`

This file is computed from the clean data before any issues were added. It contains:
- row counts and total net sales (Rs 2,533,032,735.60)
- net sales by month
- the 5 planted signals with their expected answers
- counts of every planted data-quality issue

The dbt reconciliation tests and the assistant evaluation both check against this file.
