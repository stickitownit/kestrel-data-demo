with source as (
    select * from {{ source('erp', 'customers') }}
),

city_aliases as (
    select * from {{ ref('city_aliases') }}
)

select
    s.customer_id,
    trim(s.customer_name)                          as customer_name,
    trim(s.customer_type)                          as customer_type,
    s.city                                         as city_raw,
    a.city,                                        -- canonical city from the seed
    a.warehouse_id,                                -- serving warehouse
    trim(s.area)                                   as area,
    nullif(trim(s.salesperson_id), '')             as salesperson_id,
    cast(s.credit_days as integer)                 as credit_days,
    {{ parse_date_dmy('s.created_on') }}           as created_on,
    coalesce(s.city <> a.city, true)               as is_city_corrected,
    nullif(trim(s.salesperson_id), '') is null     as is_salesperson_missing,
    s._source_file,
    s._loaded_at
from source as s
left join city_aliases as a
    on lower(trim(s.city)) = a.city_alias
