-- Planted signal 5: exactly the 9 Multan retailers in the answer key are churned.
with expected as (
    select 'C0031' as customer_id
    union all select 'C0040' as customer_id
    union all select 'C0052' as customer_id
    union all select 'C0093' as customer_id
    union all select 'C0147' as customer_id
    union all select 'C0199' as customer_id
    union all select 'C0214' as customer_id
    union all select 'C0266' as customer_id
    union all select 'C0356' as customer_id
),

actual as (
    select customer_id from {{ ref('mart_customer_activity') }} where is_churned
)

select coalesce(e.customer_id, a.customer_id) as customer_id,
       case when a.customer_id is null then 'missing' else 'unexpected' end as problem
from expected as e
full outer join actual as a on e.customer_id = a.customer_id
where e.customer_id is null or a.customer_id is null
