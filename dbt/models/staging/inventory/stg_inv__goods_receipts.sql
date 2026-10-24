with source as (
    select * from {{ source('inventory', 'goods_receipts') }}
)

select
    trim(grn_no)                             as grn_id,
    {{ parse_iso_date('receipt_date') }}     as receipt_date,
    upper(trim(warehouse))                   as warehouse_id,
    {{ clean_sku('item_code') }}             as sku,
    cast(qty_received as integer)            as qty_received,
    trim(supplier)                           as supplier,
    _source_file,
    _loaded_at
from source
