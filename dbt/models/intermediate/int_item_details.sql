select i.source_record_number, i.order_id, i.item_number, i.product_id,
       cast(o.purchased_at as date) as purchase_date, c.state, o.status,
       case when p.source_category is null then 'Uncategorized'
            else {{ title_label("coalesce(t.english_category, p.source_category)") }}
       end as category,
       case when p.source_category is null then 'Missing source category'
            when t.english_category is null then 'Portuguese fallback'
            else 'English translation' end as category_mapping,
       i.price_cents, i.freight_cents
from {{ ref('stg_items') }} i
join {{ ref('stg_orders') }} o using (order_id)
join {{ ref('stg_customers') }} c using (customer_id)
join {{ ref('stg_products') }} p using (product_id)
left join {{ ref('stg_translations') }} t on p.source_category = t.source_category
