from snowflake.snowpark import Session
import random
import pandas as pd
import numpy as np
import math

# Define batch size for optimized execution
BATCH_SIZE = 250000  
TOTAL_RECORDS = random.randint(333333, 666666)

def main(session: Session):
    # Load required dimension tables
    customer_df = session.table("DIM_CUSTOMER").to_pandas()
    inventory_df = session.table("DIM_INVENTORY_STORAGE_LOCATION").to_pandas()
    date_df = session.table("DIM_DATE").to_pandas()
    product_df = session.table("DIM_PRODUCT").to_pandas()

    # Convert DATE_ID to datetime
    date_df["DATE_ID"] = pd.to_datetime(date_df["DATE_ID"])
    product_df["LAUNCH_DATE"] = pd.to_datetime(product_df["LAUNCH_DATE"])

    # Sampled data for efficiency
    customers_sampled = customer_df.sample(n=TOTAL_RECORDS, replace=True).reset_index(drop=True)
    order_dates_sampled = date_df.sample(n=TOTAL_RECORDS, replace=True).reset_index(drop=True)

    # Define order statuses and mappings
    order_status_values = [
        "Pending", "Processing", "On Hold", "Failed", "Canceled",
        "Completed", "Refunded", "Partially Refunded", "Awaiting Fulfillment",
        "Awaiting Shipment", "Awaiting Pickup", "Shipped", "Delivered", "Returned"
    ]

    ship_status_mappings = {
        "Pending": "Pending Shipment",
        "Processing": "Processing Shipment",
        "On Hold": "Pending Shipment",
        "Failed": "No Shipment",
        "Canceled": "No Shipment",
        "Completed": "Delivered",
        "Refunded": "Returned to Sender",
        "Partially Refunded": "In Transit",
        "Awaiting Fulfillment": "Pending Shipment",
        "Awaiting Shipment": "Pending Shipment",
        "Awaiting Pickup": "Out for Delivery",
        "Shipped": "Out for Delivery",
        "Delivered": "Delivered",
        "Returned": "Returned to Sender"
    }

    order_sources = ["Amazon", "Walmart", "eBay", "Etsy", "Temu", "Instagram", "Facebook", "TikTok"]

    # Create staging table before writing final data
    session.sql("CREATE OR REPLACE TEMP TABLE STG_CUSTOMER_ORDERS AS SELECT * FROM FACT_CUSTOMER_ORDERS LIMIT 0").collect()

    # Compute number of batches
    num_batches = math.ceil(TOTAL_RECORDS / BATCH_SIZE)

    for batch_num in range(num_batches):
        print(f"Processing batch {batch_num + 1} of {num_batches}...")

        batch_size = min(BATCH_SIZE, TOTAL_RECORDS - (batch_num * BATCH_SIZE))

        # Generate unique Order IDs
        order_ids = np.array([f"ORD{str(i).zfill(7)}" for i in range(batch_num * batch_size, (batch_num + 1) * batch_size)])

        # Assign 1-5 products per order
        num_products_per_order = np.random.randint(1, 6, batch_size)
        order_ids_expanded = np.repeat(order_ids, num_products_per_order)

        # Sample products and inventory
        product_sampled = product_df.sample(n=len(order_ids_expanded), replace=True).reset_index(drop=True)
        inventory_sampled = inventory_df.sample(n=len(order_ids_expanded), replace=True).reset_index(drop=True)

        # Ensure order dates are at least 14 days after product launch
        product_sampled["MIN_ORDER_DATE"] = product_sampled["LAUNCH_DATE"] + pd.Timedelta(days=14)

        # Sample order dates ensuring they respect the MIN_ORDER_DATE constraint
        order_date_values = np.maximum(
            order_dates_sampled["DATE_ID"].values[:batch_size].repeat(num_products_per_order),
            product_sampled["MIN_ORDER_DATE"].values
        )

        # Generate order status and ship status
        order_statuses = np.random.choice(order_status_values, len(order_ids_expanded))
        ship_statuses = np.vectorize(lambda x: ship_status_mappings[x])(order_statuses)

        # Assign order amounts and shipping costs
        order_amounts = np.random.uniform(50, 500, len(order_ids_expanded))
        shipping_costs = np.random.uniform(5, 20, len(order_ids_expanded))

        # Generate order quantities
        order_qtys = np.random.randint(1, 11, len(order_ids_expanded))

        # Assign order sources
        order_sources_sampled = np.random.choice(order_sources, len(order_ids_expanded))

        # Compute is_returned flags
        is_returned_flags = np.where(np.isin(order_statuses, ["Refunded", "Returned"]), "Yes", "No")

        # Shipping scenarios
        shipping_scenarios = np.random.choice(["express", "on_time", "delayed", "pending", "backorder"], len(order_ids_expanded), p=[0.20, 0.50, 0.20, 0.05, 0.05])
        shipping_dates, estimated_arrivals, actual_arrivals = [], [], []

        for i, scenario in enumerate(shipping_scenarios):
            ship_date, estimated_arrival, actual_arrival = None, None, None
            if scenario == "express":
                ship_date = order_date_values[i]
                estimated_arrival = ship_date + pd.Timedelta(days=random.randint(1, 2))
                actual_arrival = estimated_arrival
            elif scenario == "on_time":
                ship_date = order_date_values[i] + pd.Timedelta(days=random.randint(1, 7))
                estimated_arrival = ship_date + pd.Timedelta(days=random.randint(2, 5))
                actual_arrival = estimated_arrival
            elif scenario == "delayed":
                ship_date = order_date_values[i] + pd.Timedelta(days=random.randint(5, 15))
                estimated_arrival = ship_date + pd.Timedelta(days=random.randint(3, 7))
                actual_arrival = estimated_arrival + pd.Timedelta(days=random.randint(1, 3))
            elif scenario == "backorder":
                ship_date = order_date_values[i] + pd.Timedelta(days=random.randint(15, 30))
                estimated_arrival = ship_date + pd.Timedelta(days=random.randint(5, 10))
                actual_arrival = estimated_arrival if random.random() > 0.5 else estimated_arrival + pd.Timedelta(days=random.randint(1, 3))
            elif scenario == "pending":
                ship_date, estimated_arrival, actual_arrival = None, None, None
            shipping_dates.append(ship_date)
            estimated_arrivals.append(estimated_arrival)
            actual_arrivals.append(actual_arrival)

        df = pd.DataFrame({
            "FACT_ORDER_PK": np.char.add(order_ids_expanded, "_") + product_sampled["PRODUCT_ID"].astype(str),
            "ORDER_ID": order_ids_expanded,
            "CUSTOMER_ID": customers_sampled["CUSTOMER_ID"].values[:batch_size].repeat(num_products_per_order),
            "PRODUCT_ID": product_sampled["PRODUCT_ID"],
            "ORDER_DATE_ID": order_date_values,
            "INVENTORY_STORAGE_ID": inventory_sampled["INVENTORY_STORAGE_ID"],
            "SHIPPING_DATE_ID": shipping_dates,
            "SHIPPING_ZONE": inventory_sampled["REGION"],
            "ORDER_AMOUNT": order_amounts,
            "ORDER_QTY": order_qtys,
            "SHIPPING_COST": shipping_costs,
            "SHIP_FROM_LOCATION": inventory_sampled["CITY"],
            "SHIP_TO_ADDRESS": customers_sampled["CITY"].values[:batch_size].repeat(num_products_per_order),
            "ORDER_STATUS": order_statuses,
            "SHIP_STATUS": ship_statuses,
            "DAYS_TO_DELIVER": (pd.Series(actual_arrivals) - pd.Series(shipping_dates)).dt.days,
            "IS_RETURNED": is_returned_flags,
            "ESTIMATED_ARRIVAL_DATE": estimated_arrivals,
            "ARRIVAL_DATE": actual_arrivals,
            "ORDER_SOURCE": order_sources_sampled
        })
        
        sp_df = session.create_dataframe(df)
        sp_df.write.mode('append').save_as_table("STG_CUSTOMER_ORDERS")

    session.sql("CREATE OR REPLACE TABLE FACT_CUSTOMER_ORDERS AS SELECT * FROM STG_CUSTOMER_ORDERS").collect()

    return session.table("FACT_CUSTOMER_ORDERS")
