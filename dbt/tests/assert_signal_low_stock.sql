-- Planted signal 3: KD-OIL-002 at LHE-WH is the only low-stock item, at about 3.7 days of cover.
select warehouse_id, product_sku, days_of_cover, is_low_stock
from {{ ref('mart_stock_cover') }}
where (is_low_stock and not (warehouse_id = 'LHE-WH' and product_sku = 'KD-OIL-002'))
   or (warehouse_id = 'LHE-WH' and product_sku = 'KD-OIL-002'
       and (not is_low_stock or days_of_cover not between 3.6 and 3.8))
