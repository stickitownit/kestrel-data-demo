-- Grain: one invoice line (returns included, with negative quantity and amount).
select
    invoice_line_id,
    invoice_id,
    line_no,
    invoice_date,
    invoice_month,
    doc_type,
    is_return,
    customer_id,
    salesperson_id,
    city,
    warehouse_id,
    product_sku,
    sku_original,
    is_unknown_product,
    quantity,
    unit_price_pkr,
    discount_pct,
    gross_amount_pkr,
    discount_amount_pkr,
    net_amount_pkr,
    cost_amount_pkr
from {{ ref('int_sales_lines_enriched') }}
