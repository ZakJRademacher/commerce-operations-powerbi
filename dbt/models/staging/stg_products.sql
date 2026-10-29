select source_record_number,
       nullif(trim(product_id), '') as product_id,
       nullif(trim(product_category_name), '') as source_category
from {{ source('olist', 'products') }}
