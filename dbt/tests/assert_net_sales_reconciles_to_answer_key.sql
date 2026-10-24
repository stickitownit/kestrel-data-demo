-- Reconciliation: total net sales in the fact table must equal the answer key
-- (data/answer_key.json) within Rs 1. Returns a row (= failure) otherwise.
select
    total_net_sales_pkr,
    {{ var('answer_key_net_sales_pkr') }} as expected_pkr
from (select sum(net_amount_pkr) as total_net_sales_pkr from {{ ref('fct_sales_lines') }}) as t
where abs(total_net_sales_pkr - {{ var('answer_key_net_sales_pkr') }}) > {{ var('answer_key_tolerance_pkr') }}
