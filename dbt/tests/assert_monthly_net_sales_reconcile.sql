-- Reconciliation by month: every month in the answer key must match within Rs 1,
-- and no month may be missing on either side.
with actual as (
    select invoice_month as month_start, sum(net_amount_pkr) as net_sales_pkr
    from {{ ref('fct_sales_lines') }}
    group by invoice_month
),

expected as (
    select month_start, net_sales_pkr from {{ ref('answer_key_monthly_net_sales') }}
)

select
    coalesce(e.month_start, a.month_start) as month_start,
    e.net_sales_pkr as expected_pkr,
    a.net_sales_pkr as actual_pkr
from expected as e
full outer join actual as a on e.month_start = a.month_start
where a.net_sales_pkr is null
   or e.net_sales_pkr is null
   or abs(a.net_sales_pkr - e.net_sales_pkr) > {{ var('answer_key_tolerance_pkr') }}
