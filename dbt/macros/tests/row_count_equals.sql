{# Fails when the model does not have exactly `expected` rows. #}
{% test row_count_equals(model, expected) %}
select actual_rows, {{ expected }} as expected_rows
from (select count(*) as actual_rows from {{ model }}) as counted
where actual_rows != {{ expected }}
{% endtest %}
