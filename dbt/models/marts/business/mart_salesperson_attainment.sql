-- Grain: salesperson x month. Actual = net sales on documents booked by the
-- salesperson. The latest month is month to date: it gets a pro-rated target
-- and is left out of the "below 85% three months running" flag.
with actuals as (
    select salesperson_id, invoice_month as month_start, sum(net_amount_pkr) as actual_pkr
    from {{ ref('fct_sales_lines') }}
    group by salesperson_id, invoice_month
),

visits as (
    select
        salesperson_id,
        visit_month as month_start,
        count(*)                                        as visits,
        sum(case when is_order then 1 else 0 end)       as order_visits
    from {{ ref('fct_visits') }}
    group by salesperson_id, visit_month
),

as_of as (
    select
        max(invoice_date) as as_of_date,
        cast({{ dbt.date_trunc('month', 'max(invoice_date)') }} as date) as current_month
    from {{ ref('fct_sales_lines') }}
),

base as (
    select
        t.salesperson_id,
        t.target_month                                  as month_start,
        t.target_pkr,
        coalesce(a.actual_pkr, 0)                       as actual_pkr,
        coalesce(v.visits, 0)                           as visits,
        coalesce(v.order_visits, 0)                     as order_visits,
        t.target_month = o.current_month                as is_month_to_date,
        case
            when t.target_month = o.current_month then
                1.0 * ({{ dbt.datediff('t.target_month', 'o.as_of_date', 'day') }} + 1)
                / {{ dbt.datediff('t.target_month', dbt.dateadd('month', 1, 't.target_month'), 'day') }}
            else 1.0
        end                                             as month_elapsed_share
    from {{ ref('fct_targets_monthly') }} as t
    cross join as_of as o
    left join actuals as a on t.salesperson_id = a.salesperson_id and t.target_month = a.month_start
    left join visits  as v on t.salesperson_id = v.salesperson_id and t.target_month = v.month_start
    where t.target_month <= o.current_month
),

scored as (
    select
        *,
        actual_pkr / nullif(target_pkr, 0)                          as attainment,
        actual_pkr / nullif(target_pkr * month_elapsed_share, 0)    as attainment_to_date,
        1.0 * order_visits / nullif(visits, 0)                      as visit_to_order_rate,
        case
            when not is_month_to_date and actual_pkr / nullif(target_pkr, 0) < 0.85 then 1
            else 0
        end                                                         as below_85_flag
    from base
),

complete_streak as (
    select
        salesperson_id,
        month_start,
        sum(below_85_flag) over (
            partition by salesperson_id order by month_start
            rows between 2 preceding and current row
        ) as below_85_last_3
    from scored
    where not is_month_to_date
)

select
    concat(s.salesperson_id, '|', cast(s.month_start as {{ dbt.type_string() }})) as attainment_id,
    s.salesperson_id,
    sp.salesperson_name,
    s.month_start,
    s.is_month_to_date,
    s.target_pkr,
    s.actual_pkr,
    s.attainment,
    s.attainment_to_date,
    s.visits,
    s.order_visits,
    s.visit_to_order_rate,
    s.below_85_flag = 1                              as is_below_85,
    coalesce(c.below_85_last_3 = 3, false)           as is_below_85_three_months_running
from scored as s
left join complete_streak as c
    on s.salesperson_id = c.salesperson_id and s.month_start = c.month_start
left join {{ ref('dim_salesperson') }} as sp on s.salesperson_id = sp.salesperson_id
