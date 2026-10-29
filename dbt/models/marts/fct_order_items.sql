-- One row per order/item-number pair. Category filters belong to this fact.
select i.order_id, i.item_number, i.product_id, i.purchase_date, i.state, i.status,
       i.category, i.category_mapping, i.price_cents, i.freight_cents,
       case when r.category_rank <= 10 then i.category else 'Other categories' end as category_group
from {{ ref('int_item_details') }} i
left join {{ ref('int_category_ranking') }} r using (category)
