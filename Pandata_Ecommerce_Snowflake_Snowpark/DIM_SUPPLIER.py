from snowflake.snowpark import Session
import random
import datetime
import pandas as pd

# Define the main function
def main(session: Session):
    # Number of suppliers to create
    num_suppliers = 20

    # Generalized supplier names for the Beauty industry
    supplier_names = [
        "Global Beauty Distributors", "Prestige Personal Care", "Universal Cosmetics Co.",
        "Prime Essentials Group", "Pure Elegance Supply Co.", "Elegant Beauty Suppliers",
        "Radiance Distributors", "Infinity Beauty Co.", "Premium Distributors",
        "Natural Glow Supply Co.", "Deluxe Beauty Group", "Fresh Glow Distributors",
        "Luxury Essentials", "Elite Beauty Providers", "Harmony Beauty Group",
        "Timeless Distributors", "Serenity Beauty Co.", "Modern Beauty Solutions",
        "Exquisite Beauty Group", "Venus Distributors"
    ]

    # Supplier locations and countries
    supplier_locations = {
        "China": ["Shanghai", "Beijing", "Shenzhen", "Guangzhou", "Chengdu"],
        "USA": ["New York", "Los Angeles", "Chicago", "Houston", "San Francisco"],
        "South Korea": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"],
        "France": ["Paris", "Lyon", "Marseille", "Nice", "Toulouse"],
        "Germany": ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt"],
        "Japan": ["Tokyo", "Osaka", "Kyoto", "Nagoya", "Hiroshima"],
        "India": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"]
    }

    # Contact names by country
    contact_names_by_country = {
        "China": {"first_names": ["Wei", "Li", "Chen"], "last_names": ["Wang", "Zhang", "Liu"]},
        "USA": {"first_names": ["James", "Mary", "John"], "last_names": ["Smith", "Johnson", "Brown"]},
        "South Korea": {"first_names": ["Ji-hoon", "Min-ji", "Hyeon"], "last_names": ["Kim", "Lee", "Park"]},
        "France": {"first_names": ["Jean", "Marie", "Pierre"], "last_names": ["Dubois", "Moreau", "Lefevre"]},
        "Germany": {"first_names": ["Hans", "Anna", "Klaus"], "last_names": ["Schmidt", "Müller", "Weber"]},
        "Japan": {"first_names": ["Hiroshi", "Yuki", "Satoshi"], "last_names": ["Tanaka", "Yamamoto", "Kobayashi"]},
        "India": {"first_names": ["Ravi", "Priya", "Anil"], "last_names": ["Sharma", "Gupta", "Kumar"]}
    }

    supplier_types = ["Manufacturer", "Distributor", "Wholesaler", "Retailer"]
    email_domains = ["supplier.com", "distributor.net", "wholesaler.org", "retailer.biz"]

    # Function to generate supplier data
    def generate_supplier_data():
        data = []
        start_date = datetime.date(2020, 1, 1)  # Data is strictly from 2020

        for i in range(num_suppliers):
            supplier_id = f"SUP{random.randint(100, 999)}"  # Unique supplier ID
            country = random.choice(list(supplier_locations.keys()))
            city = random.choice(supplier_locations[country])
            supplier_name = supplier_names[i % len(supplier_names)]  # Rotate through supplier names

            # Generate contact name based on country
            contact_first_name = random.choice(contact_names_by_country[country]["first_names"])
            contact_last_name = random.choice(contact_names_by_country[country]["last_names"])
            contact_name = f"{contact_first_name} {contact_last_name}"

            contact_email = f"{contact_first_name.lower()}.{contact_last_name.lower()}@{random.choice(email_domains)}"
            supplier_type = random.choice(supplier_types)

            # Related date should be strictly within 2020
            related_date = start_date + datetime.timedelta(days=random.randint(0, 366))

            # Determine if the supplier is local (e.g., USA is local)
            is_local = "Yes" if country == "USA" else "No"

            # Append supplier data
            data.append({
                "SUPPLIER_ID": supplier_id,
                "SUPPLIER_NAME": supplier_name,
                "SUPPLIER_CITY": city,
                "SUPPLIER_TYPE": supplier_type,
                "CONTACT_NAME": contact_name,
                "CONTACT_EMAIL": contact_email,
                "COUNTRY": country,
                "RELATIONSHIP_ESTABLISH_DATE": related_date,
                "IS_LOCAL": is_local
            })
        return data

    # Generate supplier data
    supplier_data = generate_supplier_data()

    # Create a Pandas DataFrame
    df = pd.DataFrame(supplier_data)

    # Convert Pandas DataFrame to Snowpark DataFrame
    sp_df = session.create_dataframe(df)

    # Write the DataFrame to the DIM_SUPPLIER table in Snowflake
    sp_df.write.mode('overwrite').save_as_table("DIM_SUPPLIER")

    # Return the Snowpark DataFrame
    return session.table("DIM_SUPPLIER")
