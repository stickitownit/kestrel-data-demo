with source as (
    select * from {{ source('field_app', 'visits') }}
),

-- App sync retries send the same visit more than once. Keep the first copy.
ranked as (
    select
        *,
        row_number() over (partition by visit_id order by _row_number) as copy_no
    from source
)

select
    trim(visit_id)                                       as visit_id,
    trim(salesperson_id)                                 as salesperson_id,
    trim(customer_id)                                    as customer_id,
    {{ parse_utc('visited_at_utc') }}                    as visited_at_utc,
    {{ utc_to_pkt('visited_at_utc') }}                   as visited_at_pkt,
    -- Join to ERP invoice dates on this local (Pakistan) date, not the UTC one.
    cast({{ utc_to_pkt('visited_at_utc') }} as date)     as visit_date,
    trim(outcome)                                        as outcome,
    nullif(trim(order_ref), '')                          as order_ref,
    _source_file,
    _loaded_at
from ranked
where copy_no = 1
