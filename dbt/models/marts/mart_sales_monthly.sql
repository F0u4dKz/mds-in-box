{{ config(materialized="view") }}

with
    fact as (select * from {{ ref("int_fact_orders") }}),

    monthly as (
        select
            date_trunc('month', purchased_at)::date as purchase_month,
            sum(order_amount) as revenue,
            count(distinct order_id) as order_count
        from fact
        group by 1
    ),

    with_kpis as (
        select
            purchase_month,
            revenue,
            order_count,
            revenue / nullif(order_count, 0) as aov,
            lag(revenue) over (order by purchase_month) as previous_revenue
        from monthly
    )

select
    purchase_month,
    revenue,
    order_count,
    aov,
    (revenue - previous_revenue) / nullif(previous_revenue, 0) as revenue_mom_rate
from with_kpis
