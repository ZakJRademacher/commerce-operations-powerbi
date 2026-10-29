{% macro money_cents(column_name) %}
-- Accept plain nonnegative decimal text, including redundant trailing zeroes.
-- Reject extra nonzero precision rather than rounding it.
case when regexp_full_match(trim({{ column_name }}), '[+]?[0-9]+([.][0-9]{0,2}0*)?')
     then cast(cast(trim({{ column_name }}) as decimal(20,2)) * 100 as bigint)
end
{% endmacro %}

{% macro exact_integer(column_name) %}
case when regexp_full_match(trim({{ column_name }}), '[+-]?[0-9]+')
     then try_cast(trim({{ column_name }}) as integer)
end
{% endmacro %}

{% macro title_label(expression) %}
array_to_string(
    list_transform(string_split(replace({{ expression }}, '_', ' '), ' '),
                   word -> upper(left(word, 1)) || lower(substr(word, 2))),
    ' ')
{% endmacro %}

{% test non_negative(model, column_name) %}
select * from {{ model }} where {{ column_name }} < 0
{% endtest %}

{% test combination_unique(model, columns) %}
select {{ columns | join(', ') }}, count(*) as copies
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
