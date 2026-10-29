-- Separate aggregation avoids item x payment fan-out.
select order_id, count(*)::bigint as payment_rows,
       sum(payment_cents)::bigint as payment_cents
from {{ ref('stg_payments') }}
group by order_id
