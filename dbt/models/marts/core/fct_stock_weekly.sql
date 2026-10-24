-- Grain: warehouse x SKU x week (week ends Sunday, as in the stock report).
-- Units sold and received are for the 7 days ending on week_ending.
with stock as (
    select * from {{ ref('stg_inv__stock_snapshots') }}
),

sales as (
    select
        s.warehouse_id,
        s.sku,
        s.week_ending,
        sum(l.quantity) as units_sold
    from stock as s
    inner join {{ ref('int_sales_lines_enriched') }} as l
        on  l.warehouse_id = s.warehouse_id
        and l.sku_original = s.sku
        and l.invoice_date >  cast({{ dbt.dateadd('day', -7, 's.week_ending') }} as date)
        and l.invoice_date <= s.week_ending
    group by s.warehouse_id, s.sku, s.week_ending
),

receipts as (
    select
        s.warehouse_id,
        s.sku,
        s.week_ending,
        sum(g.qty_received) as units_received
    from stock as s
    inner join {{ ref('stg_inv__goods_receipts') }} as g
        on  g.warehouse_id = s.warehouse_id
        and g.sku = s.sku
        and g.receipt_date >  cast({{ dbt.dateadd('day', -7, 's.week_ending') }} as date)
        and g.receipt_date <= s.week_ending
    group by s.warehouse_id, s.sku, s.week_ending
)

select
    concat(s.warehouse_id, '|', s.sku, '|', cast(s.week_ending as {{ dbt.type_string() }})) as stock_week_id,
    s.warehouse_id,
    s.sku                                   as sku_original,
    case when p.sku is null then 'UNKNOWN' else s.sku end as product_sku,
    s.week_ending,
    s.closing_qty,
    coalesce(sa.units_sold, 0)              as units_sold,
    coalesce(r.units_received, 0)           as units_received
from stock as s
left join {{ ref('stg_erp__products') }} as p on s.sku = p.sku
left join sales as sa
    on s.warehouse_id = sa.warehouse_id and s.sku = sa.sku and s.week_ending = sa.week_ending
left join receipts as r
    on s.warehouse_id = r.warehouse_id and s.sku = r.sku and s.week_ending = r.week_ending
