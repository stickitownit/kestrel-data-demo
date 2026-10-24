select
    c.customer_id,
    c.customer_name,
    c.customer_type,
    c.city,
    c.warehouse_id,
    c.area,
    coalesce(c.salesperson_id, 'UNASSIGNED')        as salesperson_id,
    coalesce(s.salesperson_name, 'Unassigned')      as salesperson_name,
    c.credit_days,
    c.created_on,
    c.is_city_corrected,
    c.is_salesperson_missing
from {{ ref('stg_erp__customers') }} as c
left join {{ ref('stg_app__salespeople') }} as s on c.salesperson_id = s.salesperson_id
