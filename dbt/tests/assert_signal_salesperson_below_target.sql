-- Planted signal 2: at the latest complete month, SP-07 is the only salesperson
-- below 85% of target three months running.
with latest_complete as (
    select max(month_start) as month_start
    from {{ ref('mart_salesperson_attainment') }}
    where not is_month_to_date
),

flagged as (
    select m.salesperson_id
    from {{ ref('mart_salesperson_attainment') }} as m
    inner join latest_complete as l on m.month_start = l.month_start
    where m.is_below_85_three_months_running
)

select 'unexpected' as problem, salesperson_id from flagged where salesperson_id <> 'SP-07'
union all
select 'SP-07 not flagged', 'SP-07'
from (select count(*) as n from flagged where salesperson_id = 'SP-07') as c
where c.n = 0
