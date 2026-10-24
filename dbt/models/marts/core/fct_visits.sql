-- Grain: one shop visit (duplicates already removed in staging).
select
    v.visit_id,
    v.salesperson_id,
    v.customer_id,
    v.visit_date,                                   -- Pakistan date
    cast({{ dbt.date_trunc('month', 'v.visit_date') }} as date) as visit_month,
    v.visited_at_pkt,
    v.outcome,
    v.outcome = 'order'                             as is_order,
    v.order_ref,
    i.invoice_id is not null                        as is_order_ref_matched
from {{ ref('stg_app__visits') }} as v
left join {{ ref('stg_erp__invoices') }} as i on v.order_ref = i.invoice_id
