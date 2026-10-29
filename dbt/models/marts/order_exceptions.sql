-- An order may have multiple exception events. Do not sum these as distinct orders.
select order_id, 'Delivered order excluded from timing' as rule,
       'Missing actual/estimated date or actual delivery precedes purchase' as detail
from {{ ref('int_order_details') }}
where source_status = 'delivered' and not is_delivery_eligible
union all
select order_id, 'Delivery precedes purchase', 'Source timestamp retained; timing excluded'
from {{ ref('int_order_details') }} where delivered_at < purchased_at
union all
select order_id, 'Status/date conflict', 'Actual delivery present for a non-delivered status'
from {{ ref('int_order_details') }} where source_status <> 'delivered' and delivered_at is not null
union all
select order_id, 'No item lines', 'Order retained with zero merchandise and zero freight'
from {{ ref('int_order_details') }} where item_count = 0
union all
select order_id, 'No payment rows', 'Payment amount left blank'
from {{ ref('int_order_details') }} where payment_cents is null
union all
select order_id, 'Payment differs from items plus freight',
       printf('Difference BRL %.2f; no forced reconciliation', payment_difference_cents / 100.0)
from {{ ref('int_order_details') }} where payment_difference_cents <> 0
