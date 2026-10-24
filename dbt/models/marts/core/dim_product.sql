-- Product master plus one "Unknown product" row for SKUs missing from the master.
select
    sku                 as product_sku,
    product_name,
    category,
    brand,
    pack_size,
    unit_price_pkr,
    unit_cost_pkr,
    units_per_carton,
    is_active
from {{ ref('stg_erp__products') }}

union all

select
    'UNKNOWN'           as product_sku,
    'Unknown product'   as product_name,
    'Unknown'           as category,
    'Unknown'           as brand,
    null                as pack_size,
    null                as unit_price_pkr,
    null                as unit_cost_pkr,
    null                as units_per_carton,
    false               as is_active
