select * from {{ ref('fct_orders') }}
where payment_difference_cents is distinct from
      payment_cents - merchandise_cents - freight_cents
