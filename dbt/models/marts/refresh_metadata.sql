select min(snapshot_id) as snapshot,
       min(loaded_at_utc) as built_utc,
       (select count(*) from {{ ref('fct_orders') }}) as source_orders,
       (select count(*) from {{ ref('fct_order_items') }}) as source_items,
       (select count(*) from {{ ref('order_exceptions') }}) as exception_events,
       (select count(distinct order_id) from {{ ref('order_exceptions') }}) as orders_with_exceptions
from {{ source('olist', 'ingestion_metadata') }}
