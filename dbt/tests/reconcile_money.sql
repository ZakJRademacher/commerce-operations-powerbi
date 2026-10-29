select 'merchandise' as failed_check
where coalesce((select sum(merchandise_cents) from {{ ref('fct_orders') }}), 0)
   <> coalesce((select sum(price_cents) from {{ ref('stg_items') }}), 0)
union all
select 'freight'
where coalesce((select sum(freight_cents) from {{ ref('fct_orders') }}), 0)
   <> coalesce((select sum(freight_cents) from {{ ref('stg_items') }}), 0)
union all
select 'payments'
where coalesce((select sum(payment_cents) from {{ ref('fct_orders') }}), 0)
   <> coalesce((select sum(payment_cents) from {{ ref('stg_payments') }}), 0)
