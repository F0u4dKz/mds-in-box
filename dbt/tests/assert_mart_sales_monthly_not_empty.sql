-- Fixture CI should always produce at least one monthly mart row.
select 1
from {{ ref('mart_sales_monthly') }}
having count(*) = 0
