-- Workload and service rate answer different questions.
select state, count(*) as orders, sum(delivery_eligible) as eligible_deliveries,
       sum(late) as late_deliveries,
       round(100.0 * sum(late) / nullif(sum(delivery_eligible), 0), 2) as late_percent
from {{ ref('fct_orders') }}
group by state
order by late_deliveries desc
