from snowflake.snowpark import Session
import random
import datetime
import pandas as pd

# Define the main function
def main(session: Session):
    # Load unique SUPPLIER_IDs from DIM_SUPPLIER
    supplier_df = session.table("DIM_SUPPLIER").to_pandas()
    supplier_ids = supplier_df["SUPPLIER_ID"].unique().tolist()

    # Categories, subcategories, and product names for the Beauty industry
    category_subcategory_mapping = {
        "Skincare": {
            "Moisturizers": ["Hydrating Face Cream", "Anti-Aging Night Cream", "Vitamin C Day Cream"],
            "Cleansers": ["Gentle Foaming Cleanser", "Deep Cleansing Gel", "Micellar Water"],
            "Serums": ["Hyaluronic Acid Serum", "Retinol Repair Serum", "Brightening Vitamin C Serum"],
            "Face Masks": ["Charcoal Detox Mask", "Hydrating Sheet Mask", "Clay Purifying Mask"]
        },
        "Hair Care": {
            "Shampoos": ["Nourishing Argan Oil Shampoo", "Tea Tree Anti-Dandruff Shampoo", "Color Protect Shampoo"],
            "Conditioners": ["Repairing Keratin Conditioner", "Volumizing Hair Conditioner", "Moisture Boost Conditioner"],
            "Hair Oils": ["Coconut Hair Oil", "Moroccan Argan Hair Oil", "Amla Nourishing Hair Oil"],
            "Hair Treatments": ["Keratin Hair Mask", "Deep Conditioning Treatment", "Frizz Control Serum"]
        },
        "Makeup": {
            "Lipsticks": ["Matte Velvet Lipstick", "Hydrating Lip Gloss", "Long-Wear Lip Crayon"],
            "Foundations": ["Full Coverage Foundation", "Lightweight BB Cream", "Dewy Finish Liquid Foundation"],
            "Mascaras": ["Volume Boost Mascara", "Waterproof Lengthening Mascara", "Lash Defining Mascara"],
            "Blushes": ["Rose Glow Blush", "Peach Perfect Blush", "Berry Cheek Tint"]
        },
        "Fragrances": {
            "Perfumes": ["Fresh Floral Eau de Parfum", "Citrus Splash Eau de Toilette", "Warm Amber Fragrance"],
            "Body Mists": ["Tropical Coconut Mist", "Lavender Breeze Mist", "Fruity Blossom Mist"],
            "Eau de Parfum": ["Luxury Oud Parfum", "Sensual Vanilla Parfum", "Ocean Breeze Parfum"],
            "Roll-Ons": ["Citrus Fresh Roll-On", "Herbal Calm Roll-On", "Musky Night Roll-On"]
        },
        "Organic Products": {
            "Organic Soaps": ["Handmade Lavender Soap", "Charcoal Detox Soap", "Neem Herbal Soap"],
            "Natural Oils": ["Cold Pressed Almond Oil", "Extra Virgin Coconut Oil", "Argan Glow Oil"],
            "Herbal Creams": ["Aloe Vera Soothing Cream", "Turmeric Healing Cream", "Calendula Skin Balm"],
            "Eco-Friendly Makeup": ["Bamboo Lip Balm", "Natural Mineral Foundation", "Eco-Friendly Mascara"]
        }
    }

    # Brands associated with the products
    brands = [
        "L'Oréal", "Estée Lauder", "Shiseido", "Unilever", "Dior",
        "Chanel", "Clarins", "MAC Cosmetics", "Clinique", "Neutrogena",
        "Nivea", "Maybelline", "Revlon", "Biotique", "Forest Essentials",
        "SK-II", "Florasis", "Huda Beauty", "Laneige", "Tatcha"
    ]

    # Function to generate product data
    def generate_product_data(num_records=100):
        data = []

        # Define launch date range
        launch_start_date = datetime.date(2021, 1, 1)
        launch_end_date = datetime.date(2021, 12, 31)

        for _ in range(num_records):
            category = random.choice(list(category_subcategory_mapping.keys()))
            subcategory = random.choice(list(category_subcategory_mapping[category].keys()))
            product_name = random.choice(category_subcategory_mapping[category][subcategory])
            brand = random.choice(brands)
            product_id = f"PROD{random.randint(100000, 999999)}"

            # Set LAUNCH_DATE
            launch_date = launch_start_date + datetime.timedelta(
                days=random.randint(0, (launch_end_date - launch_start_date).days)
            )

            # PRICE_UPDATED_DATE happens after LAUNCH_DATE
            price_updated_date = launch_date + datetime.timedelta(days=random.randint(30, 365))

            cost_price = round(random.uniform(5, 200), 2)
            retail_price = round(cost_price * random.uniform(1.5, 3.0), 2)
            supplier_id = random.choice(supplier_ids)

            # Calculate IS_ACTIVE based on the LAUNCH_DATE
            is_active = "Yes" if launch_date <= datetime.date.today() else "No"

            # Append product data
            data.append({
                "PRODUCT_ID": product_id,
                "PRODUCT_NAME": f"{brand} {product_name}",
                "BRAND": brand,
                "CATEGORY": category,
                "SUBCATEGORY": subcategory,
                "COST_PRICE": cost_price,
                "RETAIL_PRICE": retail_price,
                "SUPPLIER_ID": supplier_id,
                "LAUNCH_DATE": launch_date.strftime('%Y-%m-%d'),
                "PRICE_UPDATED_DATE": price_updated_date.strftime('%Y-%m-%d'),
                "IS_ACTIVE": is_active
            })
        return data

    # Generate product data
    product_data = generate_product_data()

    # Create a Pandas DataFrame
    df = pd.DataFrame(product_data)

    # Convert Pandas DataFrame to Snowpark DataFrame
    sp_df = session.create_dataframe(df)

    # Write the DataFrame to the DIM_PRODUCT table in Snowflake
    sp_df.write.mode('overwrite').save_as_table("DIM_PRODUCT")

    # Return the Snowpark DataFrame
    return session.table("DIM_PRODUCT")
