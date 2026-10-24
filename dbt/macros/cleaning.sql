{# Cleaning helpers used by the staging models.
   Each one has a DuckDB (default) version and a BigQuery version so the same
   models run on both targets. #}

{# 'DD/MM/YYYY' text -> DATE. Fails loudly on anything that doesn't parse. #}
{% macro parse_date_dmy(col) %}{{ return(adapter.dispatch('parse_date_dmy', 'kestrel')(col)) }}{% endmacro %}
{% macro default__parse_date_dmy(col) %}cast(strptime({{ col }}, '%d/%m/%Y') as date){% endmacro %}
{% macro bigquery__parse_date_dmy(col) %}parse_date('%d/%m/%Y', {{ col }}){% endmacro %}

{# 'YYYY-MM-DD' (optionally followed by a time) -> DATE. Portable SQL. #}
{% macro parse_iso_date(col) %}cast(substr({{ col }}, 1, 10) as date){% endmacro %}

{# Money as text, e.g. '12,345.00' -> exact decimal with 2 places. #}
{% macro to_money(col) %}cast(replace(trim({{ col }}), ',', '') as {{ kestrel.type_money() }}){% endmacro %}
{% macro type_money() %}{{ return(adapter.dispatch('type_money', 'kestrel')()) }}{% endmacro %}
{% macro default__type_money() %}decimal(18, 2){% endmacro %}
{% macro bigquery__type_money() %}numeric{% endmacro %}

{# Rates such as discount_pct ('0.03') -> exact decimal. #}
{% macro to_rate(col) %}cast(trim({{ col }}) as {{ kestrel.type_rate() }}){% endmacro %}
{% macro type_rate() %}{{ return(adapter.dispatch('type_rate', 'kestrel')()) }}{% endmacro %}
{% macro default__type_rate() %}decimal(9, 6){% endmacro %}
{% macro bigquery__type_rate() %}numeric{% endmacro %}

{# ISO-8601 UTC text '2025-07-01T04:03:00Z' -> timestamp (UTC). #}
{% macro parse_utc(col) %}{{ return(adapter.dispatch('parse_utc', 'kestrel')(col)) }}{% endmacro %}
{% macro default__parse_utc(col) %}strptime({{ col }}, '%Y-%m-%dT%H:%M:%SZ'){% endmacro %}
{% macro bigquery__parse_utc(col) %}timestamp({{ col }}){% endmacro %}

{# ISO-8601 UTC text -> local Pakistan time (Asia/Karachi, UTC+5).
   Pakistan has not used daylight saving since 2009, so on DuckDB a fixed
   +5h offset is exact and avoids depending on the ICU time-zone extension. #}
{% macro utc_to_pkt(col) %}{{ return(adapter.dispatch('utc_to_pkt', 'kestrel')(col)) }}{% endmacro %}
{% macro default__utc_to_pkt(col) %}({{ kestrel.parse_utc(col) }} + interval 5 hour){% endmacro %}
{% macro bigquery__utc_to_pkt(col) %}datetime(timestamp({{ col }}), 'Asia/Karachi'){% endmacro %}

{# SKU codes: trim, upper-case, and restore dashes on codes like 'KDOIL001'
   (ISB warehouse format) -> 'KD-OIL-001'. Portable SQL. #}
{% macro clean_sku(col) -%}
case
    when strpos(upper(trim({{ col }})), '-') = 0 and length(trim({{ col }})) = 8
        then concat(
            substr(upper(trim({{ col }})), 1, 2), '-',
            substr(upper(trim({{ col }})), 3, 3), '-',
            substr(upper(trim({{ col }})), 6, 3)
        )
    else upper(trim({{ col }}))
end
{%- endmacro %}
