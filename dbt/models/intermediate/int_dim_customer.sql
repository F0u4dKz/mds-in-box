{{ config(materialized='table') }}

with customer as (
    select * from {{ ref('fng_customer') }}
),

deduplicated as (
    select
        customer_unique_id,
        any_value(customer_city) as customer_city,
        any_value(customer_state) as customer_state
    from customer
    group by customer_unique_id
)

select * from deduplicated
