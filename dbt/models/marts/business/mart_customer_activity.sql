-- Grain: customer. Orders = INV documents (returns ignored).
-- At risk: no order for var('at_risk_days')+ days; churned: var('churned_days')+ days.
-- Days are counted to the latest invoice date in the data.
with orders as (
    select customer_id, invoice_date, sum(net_amount_pkr) as net_amount_pkr
    from {{ ref('fct_sales_lines') }}
    where doc_type = 'INV'
    group by customer_id, invoice_date
),

as_of as (
    select max(invoice_date) as as_of_date from {{ ref('fct_sales_lines') }}
),

per_customer as (
    select
        customer_id,
        min(invoice_date)       as first_order_date,
        max(invoice_date)       as last_order_date,
        count(*)                as order_days,
        sum(net_amount_pkr)     as lifetime_net_pkr
    from orders
    group by customer_id
)

select
    c.customer_id,
    c.customer_name,
    c.customer_type,
    c.city,
    c.salesperson_id,
    p.first_order_date,
    p.last_order_date,
    coalesce(p.order_days, 0)                               as order_days,
    coalesce(p.lifetime_net_pkr, 0)                         as lifetime_net_pkr,
    o.as_of_date,
    {{ dbt.datediff('p.last_order_date', 'o.as_of_date', 'day') }} as days_since_last_order,
    coalesce(
        {{ dbt.datediff('p.last_order_date', 'o.as_of_date', 'day') }} >= {{ var('at_risk_days') }}
        and {{ dbt.datediff('p.last_order_date', 'o.as_of_date', 'day') }} < {{ var('churned_days') }},
        false)                                              as is_at_risk,
    coalesce({{ dbt.datediff('p.last_order_date', 'o.as_of_date', 'day') }} >= {{ var('churned_days') }}, true)
                                                            as is_churned
from {{ ref('dim_customer') }} as c
cross join as_of as o
left join per_customer as p on c.customer_id = p.customer_id
