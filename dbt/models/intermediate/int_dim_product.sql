{{ config(materialized='table') }}

with product as (
    select * from {{ ref('fng_product') }}
),

product_category_name_translation as (
    select * from {{ ref('fng_product_category_name_translation') }}
),

joined as (
    select
        product.product_id,
        coalesce(
            product_category_name_translation.product_category_name_english,
            'Unknown'
        ) as product_category_name_english
    from product
    left join product_category_name_translation
        on product_category_name_translation.product_category_name
        = product.product_category_name
)

select * from joined
