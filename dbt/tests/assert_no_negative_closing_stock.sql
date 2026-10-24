select * from {{ ref('fct_stock_weekly') }} where closing_qty < 0
