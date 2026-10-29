select rule as check_name, count(*)::bigint as rows
from {{ ref('order_exceptions') }} group by rule
union all
select 'Item lines missing source category', count(*)::bigint
from {{ ref('fct_order_items') }} where category_mapping = 'Missing source category'
union all
select 'Item lines using Portuguese fallback', count(*)::bigint
from {{ ref('fct_order_items') }} where category_mapping = 'Portuguese fallback'
