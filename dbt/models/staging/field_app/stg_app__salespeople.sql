with source as (
    select * from {{ source('field_app', 'salespeople') }}
)

select
    trim(salesperson_id)                   as salesperson_id,
    trim(name)                             as salesperson_name,
    trim(city)                             as home_city,
    {{ parse_iso_date('joined_on') }}      as joined_on,
    _source_file,
    _loaded_at
from source
