with joined as (
    select o.order_id, o.purchased_at, o.delivered_at, o.estimated_at,
           c.state, o.source_status, o.status,
           coalesce(i.item_count, 0)::bigint as item_count,
           coalesce(i.merchandise_cents, 0)::bigint as merchandise_cents,
           coalesce(i.freight_cents, 0)::bigint as freight_cents,
           p.payment_cents,
           o.source_status = 'delivered'
             and o.delivered_at is not null and o.estimated_at is not null
             and o.delivered_at >= o.purchased_at as is_delivery_eligible
    from {{ ref('stg_orders') }} o
    join {{ ref('stg_customers') }} c using (customer_id)
    left join {{ ref('int_item_totals') }} i using (order_id)
    left join {{ ref('int_payment_totals') }} p using (order_id)
)
select *,
       payment_cents - merchandise_cents - freight_cents as payment_difference_cents,
       case when is_delivery_eligible then
           date_diff('day', cast(purchased_at as date), cast(delivered_at as date))
       end::integer as delivery_days,
       case when is_delivery_eligible then
           greatest(0, date_diff('day', cast(estimated_at as date), cast(delivered_at as date)))
       end::integer as late_days
from joined
