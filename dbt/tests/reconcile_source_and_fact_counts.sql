select 'orders' as failed_check
where (select count(*) from {{ source('olist', 'orders') }})
   <> (select count(*) from {{ ref('fct_orders') }})
union all
select 'items'
where (select count(*) from {{ source('olist', 'items') }})
   <> (select count(*) from {{ ref('fct_order_items') }})
