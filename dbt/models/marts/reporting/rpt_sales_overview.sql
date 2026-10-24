-- Grain: one invoice line. A wide, dashboard-ready copy of fct_sales_lines with
-- product, customer and salesperson names joined in, so Looker Studio needs no blends.
select
    f.invoice_line_id,
    f.invoice_id,
    f.invoice_date,
    f.invoice_month,
    f.doc_type,
    f.is_return,
    f.city,
    f.warehouse_id,
    f.customer_id,
    c.customer_name,
    c.customer_type,
    f.salesperson_id,
    c.salesperson_name,
    f.product_sku,
    coalesce(p.product_name, 'Unknown product')  as product_name,
    coalesce(p.category, 'Unknown')              as category,
    p.brand,
    f.is_unknown_product,
    f.quantity,
    f.gross_amount_pkr,
    f.discount_amount_pkr,
    f.net_amount_pkr,
    f.cost_amount_pkr,
    case when f.is_return then f.net_amount_pkr else 0 end as returns_amount_pkr
from {{ ref('fct_sales_lines') }} as f
left join {{ ref('dim_product') }}  as p on f.product_sku = p.product_sku
left join {{ ref('dim_customer') }} as c on f.customer_id = c.customer_id
