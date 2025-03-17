from snowflake.snowpark import Session
import random
import datetime
import pandas as pd

# Define the main function
def main(session: Session):
    # Campaign objectives and promotion codes
    campaign_objectives = {
        "Glow Like Never Before": ("Boost Product Visibility", "SKN10"),
        "Radiant Skin Rewards": ("Drive Customer Engagement", "SKN15"),
        "Youthful Glow Essentials": ("Increase Online Sales", "SKN20"),
        "Perfect Hair Week": ("Enhance Brand Recognition", "HAIR10"),
        "Hair Revival Therapy": ("Promote New Product Launch", "HAIR15"),
        "Shiny Locks Festival": ("Increase Revenue from Hair Care", "HAIR20"),
        "Flawless Beauty Fest": ("Build Customer Loyalty", "MKP10"),
        "Makeup Masterclass": ("Educate Customers on Products", "MKP15"),
        "The Makeup Week": ("Encourage Bulk Purchases", "MKP20"),
        "Signature Scents Week": ("Expand Fragrance Market Share", "FRG10"),
        "Fragrance Extravaganza": ("Boost Seasonal Sales", "FRG15"),
        "Scented Bliss Campaign": ("Retain Loyal Customers", "FRG20"),
        "Go Green: Organic Living": ("Promote Sustainable Products", "ORG10"),
        "Organic Wellness Sale": ("Acquire New Customers", "ORG15"),
        "Nature's Best Offers": ("Drive Conversions for Organic Products", "ORG20"),
    }

    # Categories for Beauty and Personal Care campaigns
    campaign_data_by_category = {
        "Skincare": ["Glow Like Never Before", "Radiant Skin Rewards", "Youthful Glow Essentials"],
        "Hair Care": ["Perfect Hair Week", "Hair Revival Therapy", "Shiny Locks Festival"],
        "Makeup": ["Flawless Beauty Fest", "Makeup Masterclass", "The Makeup Week"],
        "Fragrances": ["Signature Scents Week", "Fragrance Extravaganza", "Scented Bliss Campaign"],
        "Organic Products": ["Go Green: Organic Living", "Organic Wellness Sale", "Nature's Best Offers"]
    }

    # Fixed list of channels to assign
    channels = ["Email", "Social Media", "Paid Ads", "Referral", "Organic Search"]

    # Target audience definitions (age range and gender)
    target_audiences = [
        ("18-24", "Female"),
        ("18-24", "Male"),
        ("25-34", "Female"),
        ("25-34", "Male"),
        ("35-44", "All"),
        ("45-54", "All"),
        ("55-64", "Female"),
        ("55-64", "Male"),
        ("65+", "All")
    ]

    # Function to generate unique campaign IDs
    def generate_unique_campaign_id(used_campaign_ids):
        while True:
            campaign_id = f"CMP{random.randint(10000, 99999)}"
            if campaign_id not in used_campaign_ids:
                used_campaign_ids.add(campaign_id)
                return campaign_id

    # Function to generate campaign data
    def generate_campaign_data():
        data = []
        current_date = datetime.date.today()
        start_date_fixed = datetime.date(2021, 1, 1)  # Ensure data starts after 2021
        used_campaign_ids = set()

        for category, campaign_names in campaign_data_by_category.items():
            # Shuffle channels to ensure unique distribution
            shuffled_channels = channels[:]
            random.shuffle(shuffled_channels)

            for i, channel in enumerate(shuffled_channels):  # Iterate through channels
                campaign_name = random.choice(campaign_names)
                objective, promotion_code = campaign_objectives[campaign_name]

                # Generate unique start and end dates
                start_date = start_date_fixed + datetime.timedelta(
                    days=random.randint(0, (current_date - start_date_fixed).days)
                )
                end_date = start_date + datetime.timedelta(days=random.choice([180, 365, 730]))  # 6 months, 1 year, 2 years

                # Ensure CREATED_AT is before START_DATE
                created_at = start_date - datetime.timedelta(days=random.randint(30, 365))

                # Generate a unique CAMPAIGN_ID
                campaign_id = generate_unique_campaign_id(used_campaign_ids)

                # Calculate IS_ACTIVE status
                is_active = "Yes" if start_date <= current_date <= end_date else "No"

                # Assign target audience randomly
                target_audience_age, target_audience_gender = random.choice(target_audiences)

                # Append data
                data.append({
                    "CAMPAIGN_ID": campaign_id,
                    "CAMPAIGN_NAME": f"{campaign_name} - {category}",
                    "CATEGORY": category,
                    "CHANNEL": channel,
                    "START_DATE": start_date,
                    "END_DATE": end_date,
                    "IS_ACTIVE": is_active,
                    "OBJECTIVE": objective,
                    "PROMOTION_CODE": promotion_code,
                    "TARGET_AUDIENCE_AGE": target_audience_age,
                    "TARGET_AUDIENCE_GENDER": target_audience_gender,
                    "CREATED_AT": created_at,
                    "ETL_UPDATED_AT": current_date
                })

        return data

    # Generate campaign data
    campaign_data = generate_campaign_data()

    # Create a Pandas DataFrame
    df = pd.DataFrame(campaign_data)

    # Convert Pandas DataFrame to Snowpark DataFrame
    sp_df = session.create_dataframe(df)

    # Write the DataFrame to the DIM_CAMPAIGN table in Snowflake
    sp_df.write.mode('overwrite').save_as_table("DIM_CAMPAIGN")

    # Return the Snowpark DataFrame
    return session.table("DIM_CAMPAIGN")
