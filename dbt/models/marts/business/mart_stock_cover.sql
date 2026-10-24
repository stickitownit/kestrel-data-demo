-- Grain: warehouse x SKU, at the latest stock snapshot.
-- Days of cover = closing stock / average units sold per day over the 28 days
-- ending on the snapshot date. Low stock = below var('low_stock_days') days.
with latest as (
    select warehouse_id, max(week_ending) as week_ending
    from {{ ref('fct_stock_weekly') }}
    group by warehouse_id
),

snap as (
    select f.*
    from {{ ref('fct_stock_weekly') }} as f
    inner join latest as l
        on f.warehouse_id = l.warehouse_id and f.week_ending = l.week_ending
),

sold_28d as (
    select
        s.warehouse_id,
        s.sku_original,
        sum(l.quantity) as units_28d
    from snap as s
    inner join {{ ref('fct_sales_lines') }} as l
        on  l.warehouse_id = s.warehouse_id
        and l.sku_original = s.sku_original
        and l.invoice_date >  cast({{ dbt.dateadd('day', -28, 's.week_ending') }} as date)
        and l.invoice_date <= s.week_ending
    group by s.warehouse_id, s.sku_original
)

select
    concat(s.warehouse_id, '|', s.sku_original)          as stock_cover_id,
    s.warehouse_id,
    s.product_sku,
    s.sku_original,
    d.product_name,
    d.category,
    s.week_ending                                         as snapshot_date,
    s.closing_qty,
    coalesce(x.units_28d, 0)                              as units_sold_28d,
    coalesce(x.units_28d, 0) / 28.0                       as avg_units_per_day_28d,
    s.closing_qty / nullif(coalesce(x.units_28d, 0) / 28.0, 0) as days_of_cover,
    coalesce(s.closing_qty / nullif(coalesce(x.units_28d, 0) / 28.0, 0) < {{ var('low_stock_days') }}, false)
                                                          as is_low_stock
from snap as s
left join sold_28d as x
    on s.warehouse_id = x.warehouse_id and s.sku_original = x.sku_original
left join {{ ref('dim_product') }} as d on s.product_sku = d.product_sku
