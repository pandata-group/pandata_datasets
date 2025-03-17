from snowflake.snowpark import Session
import random
import pandas as pd

# Define the main function
def main(session: Session):
    # Define locations by region, adding state and country information
    locations_by_region = {
        "East Coast": [("New York", "New York", "USA"), ("Boston", "Massachusetts", "USA"), ("Philadelphia", "Pennsylvania", "USA")],
        "West Coast": [("Los Angeles", "California", "USA"), ("San Francisco", "California", "USA"), ("Seattle", "Washington", "USA")],
        "Midwest": [("Chicago", "Illinois", "USA"), ("Minneapolis", "Minnesota", "USA"), ("Kansas City", "Missouri", "USA")],
        "South": [("Houston", "Texas", "USA"), ("Atlanta", "Georgia", "USA"), ("Miami", "Florida", "USA"), ("Dallas", "Texas", "USA")],
        "Asia-Pacific": [
            ("Shanghai", "Shanghai", "China"), ("Beijing", "Beijing", "China"), ("Shenzhen", "Guangdong", "China"), ("Guangzhou", "Guangdong", "China"), ("Chengdu", "Sichuan", "China"),
            ("Seoul", "Seoul", "South Korea"), ("Busan", "Busan", "South Korea"), ("Incheon", "Incheon", "South Korea"), ("Daegu", "Daegu", "South Korea"), ("Daejeon", "Daejeon", "South Korea"),
            ("Tokyo", "Tokyo", "Japan"), ("Osaka", "Osaka", "Japan"), ("Kyoto", "Kyoto", "Japan"), ("Nagoya", "Aichi", "Japan"), ("Hiroshima", "Hiroshima", "Japan"),
            ("Mumbai", "Maharashtra", "India"), ("Delhi", "Delhi", "India"), ("Bangalore", "Karnataka", "India"), ("Chennai", "Tamil Nadu", "India"), ("Hyderabad", "Telangana", "India")
        ],
        "Europe": [
            ("Paris", "Île-de-France", "France"), ("Lyon", "Auvergne-Rhône-Alpes", "France"), ("Marseille", "Provence-Alpes-Côte d'Azur", "France"), ("Nice", "Provence-Alpes-Côte d'Azur", "France"), ("Toulouse", "Occitanie", "France"),
            ("Berlin", "Berlin", "Germany"), ("Munich", "Bavaria", "Germany"), ("Hamburg", "Hamburg", "Germany"), ("Cologne", "North Rhine-Westphalia", "Germany"), ("Frankfurt", "Hesse", "Germany")
        ]
    }

    # Generate unique manager names
    manager_names = [
        f"{first} {last}" for first in ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda"]
        for last in ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Wilson"]
    ]

    # Shuffle the manager names to ensure random assignment
    random.shuffle(manager_names)

    # Generate unique storage types
    storage_types = ["Warehouse", "Fulfillment Center", "Distribution Hub"]

    # Function to generate inventory storage data
    def generate_inventory_storage_data(num_records=15):
        data = []
        used_ids = set()
        for i in range(num_records):
            while True:
                storage_id = f"INV{random.randint(100, 999)}"
                if storage_id not in used_ids:
                    used_ids.add(storage_id)
                    break

            region = random.choice(list(locations_by_region.keys()))
            city, state, country = random.choice(locations_by_region[region])

            storage_type = random.choice(storage_types)
            storage_name = f"{storage_type} {storage_id}"  # Naming based only on functionality
            manager_name = manager_names.pop()
            capacity = random.randint(10000, 50000)

            data.append({
                "INVENTORY_STORAGE_ID": storage_id,
                "INVENTORY_STORAGE_NAME": storage_name,
                "CITY": city,
                "STATE": state,
                "COUNTRY": country,
                "REGION": region,
                "MANAGER_NAME": manager_name,
                "INVENTORY_STORAGE_CAPACITY": capacity,
                "INVENTORY_STORAGE_CAPACITY_UNIT": "Cubic Feet"
            })
        return data

    inventory_storage_data = generate_inventory_storage_data()
    df = pd.DataFrame(inventory_storage_data)
    sp_df = session.create_dataframe(df)
    sp_df.write.mode('overwrite').save_as_table("DIM_INVENTORY_STORAGE_LOCATION")
    return session.table("DIM_INVENTORY_STORAGE_LOCATION")
