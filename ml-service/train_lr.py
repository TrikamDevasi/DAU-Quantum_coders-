import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os
import time

def train():
    start_time = time.time()
    print("Loading datasets for a comprehensive linear regression model...")
    
    # 1. Product Catalog
    products = pd.read_parquet('../product_catalog.parquet', columns=['sku_id', 'base_price_usd', 'inventory_count'])
    
    # 2. Competitor Feed - getting the latest competitor price per product
    competitors = pd.read_parquet('../competitor_pricing_feed.parquet', columns=['sku_id', 'competitor_price', 'price_delta_pct'])
    competitors = competitors.groupby('sku_id').agg({'competitor_price': 'mean', 'price_delta_pct': 'mean'}).reset_index()
    
    # 3. User Segment Profiles
    users = pd.read_parquet('../user_segment_profiles.parquet', columns=['user_id', 'lifetime_value_usd', 'willingness_to_pay_multiplier'])
    
    # 4. Clickstream Events
    print("Loading ~400MB clickstream data...")
    # Load only necessary columns to save memory and speed up processing
    clickstream = pd.read_parquet('../clickstream_events.parquet', 
                                  columns=['sku_id', 'user_id', 'event_type', 'price_seen_usd'])
    
    # Calculate demand velocity (purchases per sku) from the clickstream
    purchases = clickstream[clickstream['event_type'] == 'purchase'].copy()
    demand = purchases.groupby('sku_id').size().reset_index(name='demand_velocity')
    
    # Merge all 4 data sources based on the 'purchase' events 
    # We predict the uplift for successful purchases
    print("Merging features from all 4 datasets... this takes a moment.")
    data = pd.merge(purchases, products, on='sku_id', how='inner')
    data = pd.merge(data, competitors, on='sku_id', how='left').fillna({
        'competitor_price': data['base_price_usd'], 
        'price_delta_pct': 0.0
    })
    data = pd.merge(data, users, on='user_id', how='left').fillna({
        'lifetime_value_usd': users['lifetime_value_usd'].median(),
        'willingness_to_pay_multiplier': 1.0
    })
    data = pd.merge(data, demand, on='sku_id', how='left').fillna({'demand_velocity': 0})
    
    # Feature Engineering
    # Calculate a normalized demand score (0-1) to combat distribution drift
    max_purchases = data['demand_velocity'].max()
    data['demand_score'] = data['demand_velocity'] / max_purchases if max_purchases > 0 else 0
    
    # Calculate target: the realized uplift of a purchase (price_seen / base_price - 1)
    data['realized_uplift'] = (data['price_seen_usd'] - data['base_price_usd']) / data['base_price_usd']
    
    # Calculate a competitor ratio
    data['competitor_ratio'] = data['competitor_price'] / data['base_price_usd']
    
    # Define features X and target y
    features = ['demand_score', 'inventory_count', 'competitor_ratio', 'willingness_to_pay_multiplier']
    X = data[features]
    y = data['realized_uplift']
    
    print(f"Applying StandardScaler and training on {len(X)} purchase vectors...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit the linear model
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    print(f"--- Model Coefficients ---")
    for feat, coef in zip(features, model.coef_):
        print(f"  {feat}: {coef:.6f}")
    print(f"  Intercept: {model.intercept_:.6f}")
    
    # Save model and scaler
    joblib.dump({
        'model': model,
        'scaler': scaler,
        'features': features
    }, 'lr_pricing_model.pkl')
    
    elapsed = time.time() - start_time
    print(f"Model successfully trained & artifacts saved to lr_pricing_model.pkl in {elapsed:.2f} seconds.")

if __name__ == '__main__':
    train()
