from snowflake.snowpark import Session
import random
import pandas as pd
import numpy as np
import math

# Define batch size and total records
BATCH_SIZE = 250000  
TOTAL_RECORDS = random.randint(1_000_000, 2_000_000)  

# Set the minimum allowed order date (After 01-01-2021)
MIN_ORDER_DATE = pd.Timestamp("2021-01-01")

def main(session: Session):
    # Load dimension and fact tables
    supplier_df = session.table("DIM_SUPPLIER").to_pandas()
    inventory_df = session.table("DIM_INVENTORY_STORAGE_LOCATION").to_pandas()
    customer_orders_df = session.table("FACT_CUSTOMER_ORDERS").to_pandas()
    product_df = session.table("DIM_PRODUCT").to_pandas()

    # Create mappings for validation & lookups
    product_supplier_map = dict(zip(product_df["PRODUCT_ID"], product_df["SUPPLIER_ID"]))
    inventory_storage_map = dict(zip(inventory_df["INVENTORY_STORAGE_ID"], inventory_df["CITY"]))
    supplier_city_map = dict(zip(supplier_df["SUPPLIER_ID"], supplier_df["SUPPLIER_CITY"]))
    product_launch_map = dict(zip(product_df["PRODUCT_ID"], pd.to_datetime(product_df["LAUNCH_DATE"])))


    # Map PRODUCT_ID to first ARRIVAL_DATE in FACT_CUSTOMER_ORDERS
    product_first_customer_arrival = (
        customer_orders_df.groupby("PRODUCT_ID")["ARRIVAL_DATE"].min().to_dict()
    )

    # Create or replace a temporary staging table
    session.sql("CREATE OR REPLACE TEMP TABLE STG_SUPPLIER_ORDERS LIKE FACT_SUPPLIER_ORDERS").collect()

    # Helper Functions
    def get_supplier_order_status(customer_order_status):
        fulfilled_statuses = {
            "Processing", "Completed", "Refunded", "Partially Refunded",
            "Awaiting Shipment", "Awaiting Pickup", "Shipped", "Delivered", "Returned"
        }
        return "Delivered" if customer_order_status in fulfilled_statuses else "Not Delivered"

    def get_supplier_ship_status(product_id, customer_ship_status):
        if customer_ship_status in {"Delivered", "Out for Delivery", "Returned to Sender"}:
            return "Delivered"
        return customer_ship_status

    def get_payment_details(order_status, arrival_date):
        payment_methods = ["Credit Card", "Debit Card", "Bank Transfer", "PayPal"]
        payment_terms = [f"TERM{random.randint(1, 5)}"]

        if order_status == "Delivered":
            return "Paid", arrival_date, random.choice(payment_methods), random.choice(payment_terms)
        return "Pending", None, random.choice(payment_methods), random.choice(payment_terms)

    # Generate Supplier Orders Data
    def generate_supplier_orders_data(batch_size, batch_num):
        customer_orders_sample = customer_orders_df.sample(n=batch_size, replace=True).reset_index(drop=True)
        inventory_sample = inventory_df.sample(n=batch_size, replace=True).reset_index(drop=True)

        # Extract PRODUCT_ID, SUPPLIER_ID
        product_ids = customer_orders_sample["PRODUCT_ID"]
        supplier_ids = [product_supplier_map.get(pid, "UNKNOWN_SUPPLIER") for pid in product_ids]


        # Generate ORDER_DATE_ID ensuring it aligns with product launch date & after 01-01-2021
        order_dates, pre_order_flags = [], []
        for pid in product_ids:
            launch_date = product_launch_map.get(pid, MIN_ORDER_DATE)  # Ensure it's after 01-01-2021
            if random.random() < 0.2:  # 20% chance of pre-order before launch
                order_date = max(launch_date - pd.Timedelta(days=random.randint(1, 30)), MIN_ORDER_DATE)
                pre_order_flags.append("Yes")
            else:
                order_date = max(launch_date + pd.Timedelta(days=random.randint(1, 5)), MIN_ORDER_DATE)
                pre_order_flags.append("No")
            order_dates.append(order_date.date())


        # **2. Generate SHIPPING_DATE_ID (1-7 days after ORDER_DATE_ID)**
        order_dates = pd.Series(order_dates)
        shipping_dates = order_dates + pd.to_timedelta(np.random.randint(1, 7, batch_size), unit="D")

        # **3. Generate ESTIMATED_ARRIVAL_DATE (5-10 days after SHIPPING_DATE_ID)**
        est_arrival_dates = shipping_dates + pd.to_timedelta(np.random.randint(5, 10, batch_size), unit="D")


        # **4. Generate ARRIVAL_DATE (Before Customer Arrival & Max 30-Day Rule)**
        arrival_dates = []
        for i, pid in enumerate(product_ids):
            customer_arrival = product_first_customer_arrival.get(pid)
            customer_order_status = customer_orders_sample["ORDER_STATUS"][i]

            if customer_order_status in {"On Hold", "Failed", "Canceled"}:
                supplier_arrival = pd.to_datetime(order_dates[i]) + pd.Timedelta(days=random.randint(1, 15))
            elif customer_arrival:
                supplier_arrival = min(
                    pd.to_datetime(customer_arrival) - pd.Timedelta(days=random.randint(5, 15)), 
                    pd.to_datetime(order_dates[i]) + pd.Timedelta(days=30)  # Enforce 30-day rule
                )
            else:
                supplier_arrival = min(
                    pd.to_datetime(est_arrival_dates[i]) + pd.Timedelta(days=random.randint(-3, 3)),
                    pd.to_datetime(order_dates[i]) + pd.Timedelta(days=30)  # Enforce 30-day rule
                )

            arrival_dates.append(supplier_arrival.date())

        # Generate Due Date
        # **5. Generate DUE_DATE_ID (3-7 days after ARRIVAL_DATE)**
        arrival_dates = pd.Series(arrival_dates)
        due_dates = arrival_dates + pd.to_timedelta(np.random.randint(3, 7, batch_size), unit="D")

        # Convert dates to string format
        #shipping_dates = pd.Series(shipping_dates).dt.strftime('%Y-%m-%d')
        #est_arrival_dates = pd.Series(est_arrival_dates).dt.strftime('%Y-%m-%d')
        #arrival_dates = pd.Series(arrival_dates).dt.strftime('%Y-%m-%d')
        #due_dates = pd.Series(due_dates).dt.strftime('%Y-%m-%d')

        # Assign Supplier Order Status and Ship Status
        supplier_order_statuses = [get_supplier_order_status(status) for status in customer_orders_sample["ORDER_STATUS"]]
        supplier_ship_statuses = [get_supplier_ship_status(product_ids[i], customer_orders_sample["SHIP_STATUS"][i]) for i in range(batch_size)]

        # Generate Payment Details
        payment_data = [get_payment_details(supplier_order_statuses[i], arrival_dates[i]) for i in range(batch_size)]
        payment_statuses, payment_dates, payment_methods, payment_terms = zip(*payment_data)

        # Validate Inventory Storage & Supplier Shipping City Alignment
        inventory_storage_ids = inventory_sample["INVENTORY_STORAGE_ID"]
        shipping_cities = [inventory_storage_map.get(inv_id, "UNKNOWN_LOCATION") for inv_id in inventory_storage_ids]
        ship_from_locations = [supplier_city_map.get(sid, "UNKNOWN_CITY") for sid in supplier_ids]

        # Prepare DataFrame
        df = pd.DataFrame({
            "SUPPLIER_ORDER_ID": [f"{supplier_ids[i]}_{batch_num}_{i+1}" for i in range(batch_size)],
            "SUPPLIER_ID": supplier_ids,
            "PRODUCT_ID": product_ids,
            "ORDER_DATE_ID": order_dates,
            "DUE_DATE_ID": due_dates,
            "ESTIMATED_ARRIVAL_DATE": est_arrival_dates,
            "ARRIVAL_DATE": arrival_dates,
            "SHIPPING_DATE_ID": shipping_dates,
            "SHIP_STATUS": supplier_ship_statuses,
            "SHIP_FROM_LOCATION": ship_from_locations,
            "SHIPPING_CITY": shipping_cities,
            "INVENTORY_STORAGE_ID": inventory_storage_ids,
            "ORDER_AMOUNT": np.round(np.random.uniform(100, 1000, batch_size), 2),
            "SHIPPING_COST": np.round(np.random.uniform(20, 100, batch_size), 2),
            "TOTAL_ITEMS": np.random.randint(5, 20, batch_size),
            "ORDER_QTY": np.random.randint(10, 50, batch_size),
            "ORDER_STATUS": supplier_order_statuses,
            "PRE_ORDER_FLAG": pre_order_flags,
            "PAYMENT_STATUS": payment_statuses,
            "PAYMENT_DATE": payment_dates,
            "PAYMENT_METHOD": payment_methods,
            "PAYMENT_TERMS_ID": payment_terms,
        })

        return df

    # Batch Processing
    num_batches = math.ceil(TOTAL_RECORDS / BATCH_SIZE)
    for batch_num in range(num_batches):
        df = generate_supplier_orders_data(BATCH_SIZE, batch_num)
        session.write_pandas(df, "STG_SUPPLIER_ORDERS", auto_create_table=False, overwrite=(batch_num == 0))

    session.sql("CREATE OR REPLACE TABLE FACT_SUPPLIER_ORDERS AS SELECT DISTINCT * FROM STG_SUPPLIER_ORDERS").collect()
    return session.table("FACT_SUPPLIER_ORDERS")
