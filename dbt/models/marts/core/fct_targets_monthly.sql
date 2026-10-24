-- Grain: salesperson x month.
select
    concat(salesperson_id, '|', cast(target_month as {{ dbt.type_string() }})) as target_id,
    salesperson_id,
    target_month,
    target_pkr
from {{ ref('stg_app__targets') }}
