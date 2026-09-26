{{ config(materialized='view') }}

with fact as (
    select * from {{ ref('int_fact_orders') }}
),

product as (
    select * from {{ ref('int_dim_product') }}
),

sales_by_category as (
    select
        product.product_category_name_english,
        sum(fact.order_amount) as revenue,
        sum(fact.quantity) as quantity,
        count(distinct fact.order_id) as order_count
    from fact
    inner join product
        on product.product_id = fact.product_id
    group by 1
)

select * from sales_by_category
