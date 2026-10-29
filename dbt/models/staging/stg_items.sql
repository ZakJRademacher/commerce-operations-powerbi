select source_record_number,
       nullif(trim(order_id), '') as order_id,
       {{ exact_integer('order_item_id') }} as item_number,
       nullif(trim(product_id), '') as product_id,
       {{ money_cents('price') }} as price_cents,
       {{ money_cents('freight_value') }} as freight_cents
from {{ source('olist', 'items') }}
