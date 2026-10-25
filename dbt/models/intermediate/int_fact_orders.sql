{{ config(materialized="table") }}

with
    order_items as (select * from {{ ref("fng_order_items") }}),

    orders as (select * from {{ ref("fng_orders") }}),

    customer as (select * from {{ ref("fng_customer") }}),

    joined as (
        select
            order_items.order_id,
            order_items.order_item_id,
            order_items.product_id,
            order_items.price,
            customer.customer_unique_id,
            orders.order_purchase_timestamp as purchased_at
        from order_items
        inner join orders on orders.order_id = order_items.order_id
        inner join customer on customer.customer_id = orders.customer_id
    ),

    aggregated as (
        select
            md5(concat_ws('|', order_id, customer_unique_id, product_id)) as order_hk,
            order_id,
            customer_unique_id,
            product_id,
            purchased_at,
            sum(price) as order_amount,
            count(order_item_id) as quantity
        from joined
        group by order_id, customer_unique_id, product_id, purchased_at
    )

select *
from aggregated
