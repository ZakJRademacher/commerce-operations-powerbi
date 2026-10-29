select source_record_number,
       nullif(trim(product_category_name), '') as source_category,
       nullif(trim(product_category_name_english), '') as english_category
from {{ source('olist', 'translations') }}
