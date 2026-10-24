with source as (
    select * from {{ source('inventory', 'stock_report') }}
)

select
    _sheet_name                              as warehouse_id,   -- one sheet per warehouse
    {{ parse_iso_date('week_ending') }}      as week_ending,    -- Sunday
    {{ clean_sku('item_code') }}             as sku,
    item_code                                as sku_raw,
    item_code <> {{ clean_sku('item_code') }} as is_sku_cleaned,  -- ISB-WH drops the dashes
    trim(item_description)                   as item_description,
    cast(closing_qty as integer)             as closing_qty,
    _source_file,
    _loaded_at
from source
