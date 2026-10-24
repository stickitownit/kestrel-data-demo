with source as (
    select * from {{ source('erp', 'sales_invoices') }}
)

select
    trim(invoice_id)                          as invoice_id,
    {{ parse_date_dmy('invoice_date') }}      as invoice_date,
    trim(customer_id)                         as customer_id,
    nullif(trim(salesperson_id), '')          as salesperson_id,
    upper(trim(doc_type))                     as doc_type,
    upper(trim(doc_type)) = 'RET'             as is_return,
    -- Header total as exported. Wrong on some invoices: trust the lines
    -- (reconciled in int_invoice_reconciliation).
    {{ to_money('total_amount_pkr') }}        as header_total_pkr,
    _source_file,
    _loaded_at
from source
