from snowflake.snowpark import Session
import random
import pandas as pd
import numpy as np

# Define the main function
def main(session: Session):
    # Load required dimension tables
    campaign_df = session.table("DIM_CAMPAIGN").to_pandas()
    product_df = session.table("DIM_PRODUCT").to_pandas()
    date_df = session.table("DIM_DATE").to_pandas()
    customer_df = session.table("DIM_CUSTOMER").to_pandas()

    # Filter active campaigns & products
    campaign_df = campaign_df[campaign_df["IS_ACTIVE"] == "Yes"]
    product_df = product_df[product_df["IS_ACTIVE"] == "Yes"]

    # Generate unique webpage IDs
    def generate_webpage_id(campaign, product):
        return (
            f"https://www.beautystore.com/"
            f"{campaign['CATEGORY'].replace(' ', '-').lower()}/"
            f"{product['SUBCATEGORY'].replace(' ', '-').lower()}/"
            f"{product['PRODUCT_NAME'].split()[0].replace(' ', '-').lower()}-{campaign['CAMPAIGN_ID']}"
        )

    # Number of records required
    num_records = 10000

    # Sample data efficiently
    campaigns = campaign_df.sample(num_records, replace=True).reset_index(drop=True)
    products = product_df.sample(num_records, replace=True).reset_index(drop=True)
    dates = date_df.sample(num_records, replace=True).reset_index(drop=True)
    customers = customer_df.sample(num_records, replace=True).reset_index(drop=True)

    # **Generate realistic impressions**
    impressions = np.random.randint(500, 5000, size=num_records)

    # **Click-Through Rate (CTR) Adjustments Based on Channel**
    channel_ctr_adjustment = {
        "Paid Ads": np.random.uniform(0.05, 0.12),
        "Social Media": np.random.uniform(0.10, 0.20),
        "Organic Search": np.random.uniform(0.15, 0.30),
        "Email": np.random.uniform(0.02, 0.10),
    }
    clicks = (impressions * campaigns["CHANNEL"].map(channel_ctr_adjustment)).astype(int)
    clicks = np.maximum(clicks, 1)  # Ensure at least 1 click

    # **Conversion Rate Based on Channel**
    conversion_factors = {
        "Paid Ads": np.random.uniform(0.01, 0.03),
        "Social Media": np.random.uniform(0.02, 0.05),
        "Organic Search": np.random.uniform(0.03, 0.07),
        "Email": np.random.uniform(0.05, 0.10),
    }
    conversions = (clicks * campaigns["CHANNEL"].map(conversion_factors)).astype(int)

    # **Ensure Some Records Have 0 Conversions but Every Campaign Has At Least One**
    unique_campaigns = campaigns["CAMPAIGN_ID"].unique()
    for campaign in unique_campaigns:
        campaign_mask = campaigns["CAMPAIGN_ID"] == campaign
        num_campaign_records = campaign_mask.sum()

        # Randomly assign 10% of records within a campaign to have 0 conversions
        zero_conversion_mask = np.random.rand(num_campaign_records) < 0.10
        conversions.loc[campaign_mask] = np.where(zero_conversion_mask, 0, conversions[campaign_mask])

        # Ensure at least one record per campaign has conversions
        if conversions[campaign_mask].sum() == 0:
            non_zero_index = np.random.choice(campaign_mask[campaign_mask].index, 1)
            conversions.loc[non_zero_index] = np.random.randint(1, 5)

    # **Ensure product prices match records**
    product_prices = np.random.choice(product_df["RETAIL_PRICE"].dropna().values, num_records, replace=True)

    # **Introduce ROI Variation by Campaign Type**
    roi_factors = np.where(
        campaigns["CHANNEL"] == "Organic Search",
        np.random.uniform(1.5, 3.0, num_records),  # Higher ROI for Organic Search
        np.random.uniform(0.8, 2.0, num_records)   # Lower ROI for Paid Ads & Social
    )

    # **Strictly Enforce Revenue as Zero When Conversions Are Zero**
    revenue = np.zeros(num_records)  # Initialize revenue with all zeros
    non_zero_mask = conversions > 0  # Identify records where conversions > 0

    # **Apply revenue calculation ONLY where conversions > 0**
    revenue[non_zero_mask] = np.round(conversions[non_zero_mask] * product_prices[non_zero_mask] * roi_factors[non_zero_mask], 2)

    # **Cost Per Click (CPC) Based on Channel**
    cpc_variation = {
        "Paid Ads": np.random.uniform(1.0, 3.0),
        "Social Media": np.random.uniform(0.5, 2.0),
        "Organic Search": np.random.uniform(0.7, 2.5),
        "Email": np.random.uniform(0.3, 1.0),
    }
    ad_spend = np.round(clicks * campaigns["CHANNEL"].map(cpc_variation), 2)

    # **Ensure Revenue > Ad Spend to Fix Negative ROI**
    ad_spend = np.maximum(ad_spend, 50)  # Ensure minimum spend
    revenue = np.maximum(revenue, np.where(revenue > 0, ad_spend * np.random.uniform(1.05, 3.0, num_records), 0))

    # **Cap ROI to Prevent Unrealistic Spikes**
    max_roi_factor = 5.0  # Maximum ROI of 500%
    revenue = np.minimum(revenue, ad_spend * max_roi_factor)

    # **Fix ROI to Ensure No Negative Values**
    roi = np.where(ad_spend > 0, (revenue - ad_spend) / ad_spend * 100, 0)
    roi = np.maximum(roi, -10)  # Prevent ROI from going below -10%

    # **Generate Unique Webpage IDs**
    webpage_ids = [
        generate_webpage_id(campaigns.iloc[i], products.iloc[i])
        for i in range(num_records)
    ]

    # **Create Final DataFrame**
    df = pd.DataFrame({
        "MARKETING_ID": [f"MARK{i+1}" for i in range(num_records)],  # Ensure unique IDs
        "AD_SPEND": ad_spend,
        "CAMPAIGN_ID": campaigns["CAMPAIGN_ID"],
        "DATE_ID": dates["DATE_ID"],
        "CUSTOMER_ID": customers["CUSTOMER_ID"],
        "IMPRESSIONS": impressions,
        "CLICKS": clicks,
        "CONVERSIONS": conversions,
        "REVENUE": revenue,
        "WEBPAGE_ID": webpage_ids,
        "TARGET_AUDIENCE_GENDER": campaigns["TARGET_AUDIENCE_GENDER"],
        "TARGET_AUDIENCE_AGE": campaigns["TARGET_AUDIENCE_AGE"],
        "CHANNEL": campaigns["CHANNEL"]
    })

    # **Convert Pandas DataFrame to Snowpark DataFrame and Save**
    sp_df = session.create_dataframe(df)
    sp_df.write.mode("overwrite").save_as_table("FACT_MARKETING")

    return session.table("FACT_MARKETING")
