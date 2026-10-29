-- Aggregate before joining to orders: one row per order that has item lines.
select order_id, count(*)::bigint as item_count,
       sum(price_cents)::bigint as merchandise_cents,
       sum(freight_cents)::bigint as freight_cents
from {{ ref('stg_items') }}
group by order_id
