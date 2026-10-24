-- Grain: product x city. "This month" = month to date up to the latest invoice
-- date; baseline = the 3 full months before it.
-- seasonality_adjusted_index = city's daily-rate change / rest of country's
-- daily-rate change (1.0 = same trend as everywhere else; below 0.7 = slowing).
with sales as (
    select * from {{ ref('fct_sales_lines') }} where product_sku <> 'UNKNOWN'
),

periods as (
    select
        as_of_date,
        cur_start,
        cast({{ dbt.dateadd('month', -3, 'cur_start') }} as date)  as base_start
    from (
        select
            max(invoice_date) as as_of_date,
            cast({{ dbt.date_trunc('month', 'max(invoice_date)') }} as date) as cur_start
        from sales
    ) as x
),

period_days as (
    select
        *,
        {{ dbt.datediff('cur_start', 'as_of_date', 'day') }} + 1 as cur_days,
        {{ dbt.datediff('base_start', 'cur_start', 'day') }}    as base_days
    from periods
),

city_units as (
    select
        s.product_sku,
        s.city,
        sum(case when s.invoice_date >= p.cur_start then s.quantity else 0 end)  as units_cur,
        sum(case when s.invoice_date <  p.cur_start then s.quantity else 0 end)  as units_base
    from sales as s
    cross join period_days as p
    where s.invoice_date >= p.base_start and s.invoice_date <= p.as_of_date
    group by s.product_sku, s.city
),

with_country as (
    select
        *,
        sum(units_cur)  over (partition by product_sku) - units_cur   as rest_units_cur,
        sum(units_base) over (partition by product_sku) - units_base  as rest_units_base
    from city_units
),

rates as (
    select
        w.*,
        p.as_of_date,
        p.cur_start,
        p.base_start,
        p.cur_days,
        p.base_days,
        1.0 * w.units_cur  / p.cur_days       as daily_units_cur,
        1.0 * w.units_base / p.base_days      as daily_units_base,
        (1.0 * w.units_cur / p.cur_days) / nullif(1.0 * w.units_base / p.base_days, 0)
            as city_change,
        (1.0 * w.rest_units_cur / p.cur_days) / nullif(1.0 * w.rest_units_base / p.base_days, 0)
            as rest_of_country_change
    from with_country as w
    cross join period_days as p
)

select
    concat(r.product_sku, '|', r.city)          as product_city_id,
    r.product_sku,
    d.product_name,
    d.category,
    r.city,
    r.as_of_date,
    r.cur_start,
    r.base_start,
    r.units_cur,
    r.units_base,
    r.daily_units_cur,
    r.daily_units_base,
    r.city_change,
    r.rest_of_country_change,
    r.city_change / nullif(r.rest_of_country_change, 0)          as seasonality_adjusted_index,
    coalesce(r.city_change / nullif(r.rest_of_country_change, 0) < {{ var('slowdown_index_threshold') }}, false)
                                                                 as is_slowing,
    rank() over (
        partition by r.city
        order by r.city_change / nullif(r.rest_of_country_change, 0)
    )                                                            as slowdown_rank_in_city
from rates as r
left join {{ ref('dim_product') }} as d on r.product_sku = d.product_sku
