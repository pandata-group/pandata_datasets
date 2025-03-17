from snowflake.snowpark import Session
import random
import datetime
import pandas as pd
import uuid

# Define the main function
def main(session: Session):
    # US states and their major cities
    state_city_mapping = {
        "California": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
        "New York": ["New York City", "Buffalo", "Rochester", "Albany"],
        "Texas": ["Houston", "Dallas", "Austin", "San Antonio"],
        "Florida": ["Miami", "Orlando", "Tampa", "Jacksonville"],
        "Illinois": ["Chicago", "Naperville", "Springfield", "Peoria"],
        "Pennsylvania": ["Philadelphia", "Pittsburgh", "Allentown", "Erie"],
        "Ohio": ["Columbus", "Cleveland", "Cincinnati", "Toledo"],
        "Georgia": ["Atlanta", "Augusta", "Savannah", "Athens"],
        "Michigan": ["Detroit", "Grand Rapids", "Warren", "Ann Arbor"],
        "North Carolina": ["Charlotte", "Raleigh", "Greensboro", "Durham"],
        "Virginia": ["Virginia Beach", "Norfolk", "Chesapeake", "Richmond"],
        "Washington": ["Seattle", "Spokane", "Tacoma", "Olympia"],
        "Arizona": ["Phoenix", "Tucson", "Mesa", "Chandler"],
        "Massachusetts": ["Boston", "Worcester", "Springfield", "Cambridge"],
        "Colorado": ["Denver", "Colorado Springs", "Aurora", "Fort Collins"],
        "Tennessee": ["Nashville", "Memphis", "Knoxville", "Chattanooga"],
        "Indiana": ["Indianapolis", "Fort Wayne", "Evansville", "Bloomington"],
        "Missouri": ["Kansas City", "St. Louis", "Springfield", "Columbia"],
        "Minnesota": ["Minneapolis", "Saint Paul", "Rochester", "Bloomington"],
        "Wisconsin": ["Milwaukee", "Madison", "Green Bay", "Kenosha"]
    }

    # Expanded list of names with gender mapping
    name_gender_mapping = {
        "James": "Male", "Mary": "Female", "Robert": "Male", "Patricia": "Female",
        "John": "Male", "Jennifer": "Female", "Michael": "Male", "Linda": "Female",
        "William": "Male", "Elizabeth": "Female", "David": "Male", "Barbara": "Female",
        "Richard": "Male", "Susan": "Female", "Joseph": "Male", "Jessica": "Female",
        "Thomas": "Male", "Sarah": "Female", "Charles": "Male", "Karen": "Female",
        "Christopher": "Male", "Nancy": "Female", "Daniel": "Male", "Lisa": "Female",
        "Matthew": "Male", "Ashley": "Female", "Anthony": "Male", "Kimberly": "Female",
        "Joshua": "Male", "Emily": "Female", "Andrew": "Male", "Megan": "Female",
        "Brandon": "Male", "Samantha": "Female", "Kevin": "Male", "Lauren": "Female",
        "Brian": "Male", "Stephanie": "Female", "Edward": "Male", "Nicole": "Female",
        "Pravalika":"Female", "Harshita": "Female", "Kendal": "Male", "Likhita": "Female",
        "Victor": "Male", "Ramya": "Female", "Steven": "Male", "Ally": "Female",
        "Vaishnavi": "Female", "Swetha": "Female", "Hari": "Male", "Keerthi": "Female",
        "Sumathi": "Female", "Katy": "Female", "Sumanth": "Male", "Kerry": "Female",
        "Manvi": "Female", "Poojitha": "Female", "Ashok": "Male", "Maneesha": "Female",
        
    }

    first_names = list(name_gender_mapping.keys())
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
        "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
        "Harris", "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Pidikiti", "Edugudi", 
        "Doddi", "Purra", "Russo", "Garrett", "Donthula", "Grant", "Dontireddy", "Kandimalla"
    ]

    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "aol.com"]
    customer_tiers = ["Bronze", "Silver", "Gold", "Platinum"]

    used_customer_ids = set()

    def generate_phone_number():
        return f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"

    def generate_zip_code():
        return f"{random.randint(10000, 99999)}"

    def generate_unique_customer_id():
        """Generates a unique customer ID to avoid duplicates."""
        while True:
            customer_id = f"CUST{random.randint(100000, 999999)}"
            if customer_id not in used_customer_ids:
                used_customer_ids.add(customer_id)
                return customer_id
        # Alternatively, use UUID (commented out):
        # return f"CUST{uuid.uuid4().hex[:8].upper()}"

    def generate_customer_data(num_records=10000):
        data = []
        current_date = datetime.date.today()
        one_year_ago = current_date - datetime.timedelta(days=365)

        for _ in range(num_records):
            state = random.choice(list(state_city_mapping.keys()))
            city = random.choice(state_city_mapping[state])
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            gender = name_gender_mapping[first_name]
            dob = datetime.date(
                random.randint(current_date.year - 80, current_date.year - 18),
                random.randint(1, 12),
                random.randint(1, 28)
            )
            signup_date = datetime.date(
                random.randint(2021, current_date.year),
                random.randint(1, 12),
                random.randint(1, 28)
            )
            email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"
            customer_id = generate_unique_customer_id()  # Ensure uniqueness
            phone = generate_phone_number()
            country = "USA"
            customer_tier = random.choice(customer_tiers)
            is_new_customer = "Yes" if signup_date >= one_year_ago else "No"

            data.append({
                "CUSTOMER_ID": customer_id,
                "FIRST_NAME": first_name,
                "LAST_NAME": last_name,
                "FULL_NAME": f"{first_name} {last_name}",
                "GENDER": gender,
                "DOB": dob,
                "AGE": current_date.year - dob.year,
                "EMAIL": email,
                "PHONE": phone,
                "ADDRESS": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Broadway', 'Elm St', 'Maple Ave'])}",
                "CITY": city,
                "STATE": state,
                "ZIPCODE": generate_zip_code(),
                "COUNTRY": country,
                "CUSTOMER_TIER": customer_tier,
                "SIGNUP_DATE": signup_date,
                "IS_NEW_CUSTOMER": is_new_customer  
            })
        return data

    customer_data = generate_customer_data()
    df = pd.DataFrame(customer_data)
    #df_unique = df.drop_duplicates(subset=['FIRST_NAME', 'LAST_NAME'])
    sp_df = session.create_dataframe(df)
    sp_df.write.mode('overwrite').save_as_table("DIM_CUSTOMER")

    return session.table("DIM_CUSTOMER")
