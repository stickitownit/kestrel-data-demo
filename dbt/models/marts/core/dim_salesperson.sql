select salesperson_id, salesperson_name, home_city, joined_on
from {{ ref('stg_app__salespeople') }}

union all

select 'UNASSIGNED', 'Unassigned', null, null
