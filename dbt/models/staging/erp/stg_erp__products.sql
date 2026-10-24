with source as (
    select * from {{ source('erp', 'products') }}
)

select
    {{ clean_sku('sku') }}               as sku,
    trim(product_name)                   as product_name,
    trim(category)                       as category,
    trim(brand)                          as brand,
    trim(pack_size)                      as pack_size,
    {{ to_money('unit_price_pkr') }}     as unit_price_pkr,
    {{ to_money('unit_cost_pkr') }}      as unit_cost_pkr,
    cast(units_per_carton as integer)    as units_per_carton,
    upper(trim(is_active)) = 'Y'         as is_active,
    _source_file,
    _loaded_at
from source
