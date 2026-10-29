select cast(day as date) as date,
       strftime(day, '%Y-%m') as month, year(day)::integer as year
from generate_series(
    (select min(purchase_date) from {{ ref('fct_orders') }}),
    (select max(purchase_date) from {{ ref('fct_orders') }}),
    interval 1 day
) dates(day)
