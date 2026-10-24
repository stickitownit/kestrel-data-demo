-- One row per invoice line, with its document header, customer, canonical city,
-- serving warehouse and product. Lines with a SKU missing from the product
-- master (KD-SNK-099) are kept: their revenue is real.
with lines as (
    select * from {{ ref('stg_erp__invoice_lines') }}
),

invoices as (
    select * from {{ ref('stg_erp__invoices') }}
),

customers as (
    select * from {{ ref('stg_erp__customers') }}
),

products as (
    select * from {{ ref('stg_erp__products') }}
)

select
    l.invoice_line_id,
    l.invoice_id,
    l.line_no,
    i.invoice_date,
    cast({{ dbt.date_trunc('month', 'i.invoice_date') }} as date) as invoice_month,
    i.doc_type,
    i.is_return,
    i.customer_id,
    i.salesperson_id,                       -- order booker on the document
    c.customer_type,
    c.city,
    c.warehouse_id,
    l.sku                                   as sku_original,
    case when p.sku is null then 'UNKNOWN' else l.sku end as product_sku,
    p.sku is null                           as is_unknown_product,
    p.product_name,
    p.category,
    p.brand,
    l.quantity,
    l.unit_price_pkr,
    l.discount_pct,
    l.gross_amount_pkr,
    l.discount_amount_pkr,
    l.net_amount_pkr,
    l.quantity * p.unit_cost_pkr            as cost_amount_pkr   -- null for unknown products
from lines as l
inner join invoices as i on l.invoice_id = i.invoice_id
left join customers as c on i.customer_id = c.customer_id
left join products as p on l.sku = p.sku
