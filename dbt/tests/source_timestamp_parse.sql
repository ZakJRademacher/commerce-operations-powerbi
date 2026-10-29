select s.order_id
from {{ ref('stg_orders') }} s
join {{ source('olist', 'orders') }} r on s.source_record_number = r.source_record_number
where (nullif(trim(r.order_delivered_customer_date), '') is not null and s.delivered_at is null)
   or (nullif(trim(r.order_estimated_delivery_date), '') is not null and s.estimated_at is null)
