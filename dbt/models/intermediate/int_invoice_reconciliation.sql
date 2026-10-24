-- One row per document: header total as exported vs the sum of its lines.
-- The lines are the source of truth; a difference above Rs 1 is a mismatch.
with invoices as (
    select * from {{ ref('stg_erp__invoices') }}
),

line_totals as (
    select
        invoice_id,
        count(*)               as line_count,
        sum(net_amount_pkr)    as lines_total_pkr
    from {{ ref('stg_erp__invoice_lines') }}
    group by invoice_id
)

select
    i.invoice_id,
    i.invoice_date,
    i.doc_type,
    i.customer_id,
    i.header_total_pkr,
    coalesce(t.lines_total_pkr, 0)                          as lines_total_pkr,
    coalesce(t.line_count, 0)                               as line_count,
    i.header_total_pkr - coalesce(t.lines_total_pkr, 0)     as difference_pkr,
    abs(i.header_total_pkr - coalesce(t.lines_total_pkr, 0)) > 1 as is_mismatch
from invoices as i
left join line_totals as t on i.invoice_id = t.invoice_id
