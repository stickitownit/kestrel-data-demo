with source as (
    select * from {{ source('field_app', 'monthly_targets') }}
)

select
    trim(salesperson_id)                                   as salesperson_id,
    {{ parse_iso_date("concat(trim(month), '-01')") }}     as target_month,   -- first day of month
    {{ to_money('target_pkr') }}                           as target_pkr,
    _source_file,
    _loaded_at
from source
