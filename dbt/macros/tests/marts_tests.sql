{# Returns one row per true value, so warn_if / error_if can pin an expected count. #}
{% test count_where_true(model, column_name) %}
select * from {{ model }} where {{ column_name }}
{% endtest %}

{# Fails for rows where the column is below 1. #}
{% test accepted_range_min_1(model, column_name) %}
select * from {{ model }} where {{ column_name }} < 1
{% endtest %}
