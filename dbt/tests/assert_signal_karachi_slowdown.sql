-- Planted signal 1: the two slowest products in Karachi (seasonality-adjusted)
-- are Mango Nectar 1L and Detergent 1kg, both flagged as slowing.
select product_sku, slowdown_rank_in_city, is_slowing
from {{ ref('mart_product_city_trend') }}
where city = 'Karachi'
  and (
        (slowdown_rank_in_city <= 2 and product_sku not in ('KD-JUI-001', 'KD-HOM-001'))
     or (product_sku in ('KD-JUI-001', 'KD-HOM-001') and (slowdown_rank_in_city > 2 or not is_slowing))
  )
