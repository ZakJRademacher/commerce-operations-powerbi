select strftime(purchase_date, '%Y-%m') as purchase_month,
       count(*) as orders, sum(delivery_eligible) as eligible_deliveries,
       sum(late) as late_deliveries,
       sum(case when status = 'Delivered' then merchandise_cents else 0 end) as delivered_merchandise_cents
from {{ ref('fct_orders') }}
group by purchase_month
order by purchase_month
