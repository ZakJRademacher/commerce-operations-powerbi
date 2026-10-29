-- One row per source order. Missing payments remain NULL, not zero.
select order_id, cast(purchased_at as date) as purchase_date, state, status,
       cast(delivered_at as date) as delivered_date,
       cast(estimated_at as date) as estimated_date,
       item_count, merchandise_cents, freight_cents, payment_cents,
       payment_difference_cents,
       cast(is_delivery_eligible as integer) as delivery_eligible,
       case when late_days > 0 then 1 else 0 end as late,
       delivery_days, late_days,
       case when not is_delivery_eligible then 'Not eligible'
            when delivery_days <= 7 then '01 | 0-7 days'
            when delivery_days <= 14 then '02 | 8-14 days'
            when delivery_days <= 30 then '03 | 15-30 days'
            else '04 | 31+ days' end as delivery_band
from {{ ref('int_order_details') }}
