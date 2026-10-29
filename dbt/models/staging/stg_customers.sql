select source_record_number,
       nullif(trim(customer_id), '') as customer_id,
       nullif(trim(customer_state), '') as state
from {{ source('olist', 'customers') }}
