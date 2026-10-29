-- Tie order matches first occurrence in the source item file, as in the baseline.
select category, sum(price_cents)::bigint as delivered_merchandise_cents,
       row_number() over (
           order by sum(price_cents) desc, min(source_record_number)
       ) as category_rank
from {{ ref('int_item_details') }}
where status = 'Delivered'
group by category
