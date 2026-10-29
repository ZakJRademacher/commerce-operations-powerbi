select distinct category from {{ ref('fct_order_items') }}
