with source as (
    select * from {{ source('erp', 'sales_invoice_lines') }}
),

-- The ERP export repeats some lines exactly (406 rows). Keep one copy.
-- _row_number is left out on purpose: it differs between the copies.
deduped as (
    select distinct
        invoice_id,
        line_no,
        sku,
        quantity,
        unit_price_pkr,
        discount_pct,
        _source_file,
        _loaded_at
    from source
),

typed as (
    select
        trim(invoice_id)                     as invoice_id,
        cast(line_no as integer)             as line_no,
        sku                                  as sku_raw,
        {{ clean_sku('sku') }}               as sku,
        cast(quantity as integer)            as quantity,      -- negative on returns
        {{ to_money('unit_price_pkr') }}     as unit_price_pkr,
        {{ to_rate('discount_pct') }}        as discount_pct,
        _source_file,
        _loaded_at
    from deduped
)

select
    concat(invoice_id, '-', cast(line_no as {{ dbt.type_string() }})) as invoice_line_id,
    invoice_id,
    line_no,
    sku,
    sku_raw,
    sku_raw <> sku                                          as is_sku_cleaned,
    quantity,
    unit_price_pkr,
    discount_pct,
    quantity * unit_price_pkr                               as gross_amount_pkr,
    quantity * unit_price_pkr * discount_pct                as discount_amount_pkr,
    quantity * unit_price_pkr * (1 - discount_pct)          as net_amount_pkr,
    _source_file,
    _loaded_at
from typed
