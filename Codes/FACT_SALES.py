from snowflake.snowpark import Session
import random
import pandas as pd
import numpy as np
import math

# Increase batch size for fewer iterations (faster execution)
BATCH_SIZE = 250000
TOTAL_RECORDS = random.randint(2000000, 3000000)

def main(session: Session):
    # Load required dimension and fact tables
    customer_df = session.table("DIM_CUSTOMER").to_pandas()
    product_df = session.table("DIM_PRODUCT").to_pandas()
    date_df = session.table("DIM_DATE").to_pandas()
    customer_orders_df = session.table("FACT_CUSTOMER_ORDERS").to_pandas()
    campaign_df = session.table("DIM_CAMPAIGN").to_pandas()

    # Define location-based sales tax rates
    location_tax_rates = {
        "New York": 0.08875,
        "California": 0.0725,
        "Texas": 0.0625,
        "Florida": 0.06,
        "Illinois": 0.0625,
        "DEFAULT": 0.07
    }

    # Define category-specific tax adjustments
    category_tax_adjustments = {
        "Organic Products": 0.0,  # Exempt from sales tax
        "Skincare": 0.07,
        "Hair Care": 0.07,
        "Makeup": 0.07,
        "Fragrances": 0.08  # Luxury tax for fragrances
    }

    # Function to get sales tax rate by location
    def get_location_tax_rate(store_location):
        return location_tax_rates.get(store_location, location_tax_rates["DEFAULT"])

    # Global sale counter to ensure unique SALES_ID across batches
    sale_counter = 1

    # Function to generate a batch of sales data using NumPy for faster processing
    def generate_sales_data(batch_size):
        nonlocal sale_counter
        # Sample required data in bulk from FACT_CUSTOMER_ORDERS
        customer_orders_sample = customer_orders_df.sample(n=batch_size, replace=True).reset_index(drop=True)

        # Extract aligned ORDER_ID, CUSTOMER_ID, and PRODUCT_ID
        order_ids = customer_orders_sample["ORDER_ID"]
        customer_ids = customer_orders_sample["CUSTOMER_ID"]
        product_ids = customer_orders_sample["PRODUCT_ID"]

        # Fetch product details for these specific products (ensuring alignment)
        product_sample = product_df.set_index("PRODUCT_ID").loc[product_ids].reset_index()

        # Sample from dates and campaigns (these are independent)
        dates_sample = date_df.sample(n=batch_size, replace=True).reset_index(drop=True)
        campaigns_sample = campaign_df.sample(n=batch_size, replace=True).reset_index(drop=True)

        # Generate unique SALES_IDs across batches using a global counter
        sale_ids = [f"SALE{str(sale_counter + i).zfill(7)}" for i in range(batch_size)]
        sale_counter += batch_size


        store_ids = [f"STORE{random.randint(100, 999)}" for _ in range(batch_size)]
        quantities_sold = np.random.randint(1, 6, batch_size)  # 1 to 5 items per sale
        discounts = np.round(np.random.uniform(0, 20, batch_size), 2)  # Discount percentage (0-20%)

        # Compute revenue, profit, and sales tax efficiently using NumPy
        revenues = np.round(product_sample["RETAIL_PRICE"].values * quantities_sold * (1 - discounts / 100), 2)
        profits = np.round(revenues - (product_sample["COST_PRICE"].values * quantities_sold), 2)

        # Get tax rates based on location
        store_locations = [addr.split(",")[-1].strip() for addr in customer_orders_sample["SHIP_TO_ADDRESS"]]
        location_tax_rates_arr = np.array([get_location_tax_rate(loc) for loc in store_locations])

        # Get category-based tax adjustments
        category_tax_rates = np.array([category_tax_adjustments.get(cat, location_tax_rates_arr[i]) 
                                       for i, cat in enumerate(product_sample["CATEGORY"])])
        sales_taxes = np.round(revenues * category_tax_rates, 2)

        # Prepare final DataFrame in bulk (faster than row-wise append)
        df = pd.DataFrame({
            "SALE_ID": sale_ids,
            "ORDER_ID": order_ids,
            "CUSTOMER_ID": customer_ids,
            "PRODUCT_ID": product_ids,
            "DATE_ID": dates_sample["DATE_ID"],
            "STORE_ID": store_ids,
            "CAMPAIGN_ID": campaigns_sample["CAMPAIGN_ID"],
            "QUANTITY_SOLD": quantities_sold,
            "REVENUE": revenues,
            "DISCOUNT": discounts,
            "PROFIT": profits,
            "SALES_TAX": sales_taxes,
            "PROMOTION_CODE": campaigns_sample["PROMOTION_CODE"],
            "OBJECTIVE": campaigns_sample["OBJECTIVE"]
        })

        return df

    # Optimized batch processing
    num_batches = math.ceil(TOTAL_RECORDS / BATCH_SIZE)

    for batch_num in range(num_batches):
        print(f"Processing batch {batch_num + 1} of {num_batches}...")

        # Generate batch data
        df = generate_sales_data(BATCH_SIZE)

        # Convert Pandas DataFrame to Snowpark DataFrame & insert using efficient bulk loading
        session.write_pandas(df, "FACT_SALES", auto_create_table=False, overwrite=False)

    print("Data generation completed successfully!")
    # Return the final table
    return session.table("FACT_SALES")
