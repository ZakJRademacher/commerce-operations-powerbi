select * from {{ ref('fct_orders') }}
where late > delivery_eligible
   or (delivery_eligible = 0 and (delivery_days is not null or late_days is not null))
   or (delivery_eligible = 1 and (delivery_days is null or late_days is null))
   or (delivery_eligible = 1 and late <> cast(delivered_date > estimated_date as integer))
