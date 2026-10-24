{# Monday-based week start on both targets.
   DuckDB's date_trunc('week') already starts on Monday (ISO week);
   BigQuery's WEEK starts on Sunday, so it uses ISOWEEK instead. #}
{% macro week_start(col) %}{{ return(adapter.dispatch('week_start', 'kestrel')(col)) }}{% endmacro %}
{% macro default__week_start(col) %}cast(date_trunc('week', {{ col }}) as date){% endmacro %}
{% macro bigquery__week_start(col) %}date_trunc(cast({{ col }} as date), isoweek){% endmacro %}
