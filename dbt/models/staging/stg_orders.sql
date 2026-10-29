select
    source_record_number,
    nullif(trim(order_id), '') as order_id,
    nullif(trim(customer_id), '') as customer_id,
    nullif(trim(order_status), '') as source_status,
    {{ title_label("trim(order_status)") }} as status,
    try_cast(nullif(trim(order_purchase_timestamp), '') as timestamp) as purchased_at,
    try_cast(nullif(trim(order_delivered_customer_date), '') as timestamp) as delivered_at,
    try_cast(nullif(trim(order_estimated_delivery_date), '') as timestamp) as estimated_at
from {{ source('olist', 'orders') }}
