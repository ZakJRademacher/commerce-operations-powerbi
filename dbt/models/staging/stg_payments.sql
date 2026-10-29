select source_record_number,
       nullif(trim(order_id), '') as order_id,
       {{ exact_integer('payment_sequential') }} as payment_sequence,
       {{ money_cents('payment_value') }} as payment_cents
from {{ source('olist', 'payments') }}
