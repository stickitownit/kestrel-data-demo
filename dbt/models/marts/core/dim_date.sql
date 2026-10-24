-- Calendar from the first sale to the end of next year.
with spine as (
    {{ dbt.date_spine(
        datepart="day",
        start_date="cast('2025-07-01' as date)",
        end_date="cast('2027-01-01' as date)"
    ) }}
)

select
    cast(date_day as date)                                          as date_day,
    {{ kestrel.week_start('date_day') }}                            as week_start,   -- Monday on both targets
    cast({{ dbt.date_trunc('month', 'date_day') }} as date)         as month_start,
    extract(year from date_day)                                     as year,
    extract(month from date_day)                                    as month,
    extract(day from date_day)                                      as day_of_month
from spine
