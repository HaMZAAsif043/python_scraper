import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Import configuration from the project
from src.config import PATHS

def load_price_data():
    """
    Load price data from CSV for visualization.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(base_dir, PATHS['processed_data'])
    reports_dir = os.path.join(base_dir, PATHS['reports'])
    os.makedirs(reports_dir, exist_ok=True)
    
    # Load the price data
    price_csv = os.path.join(processed_dir, "coffee_shops_prices_latest.csv")
    if not os.path.exists(price_csv):
        print("Price CSV file not found. Run data conversion first.")
        return None
    
    # Read the CSV into a pandas DataFrame
    df = pd.read_csv(price_csv)
    print(f"Loaded {len(df)} records from price data CSV")
    
    return df

def preprocess_price_data(df):
    """
    Preprocess the price data for visualization.
    """
    if df is None or len(df) == 0:
        return None
    
    # Filter to just rows with price information
    price_df = df.copy()
    
    # Process item_price field - convert to numeric
    price_df['numeric_price'] = None
    if 'item_price' in price_df.columns:
        # Extract numeric values from price strings
        price_df['numeric_price'] = price_df['item_price'].astype(str).str.extract(r'(\d+)').astype(float)
    
    # If no numeric prices, try to use price_level
    if price_df['numeric_price'].isnull().all() and 'price_level' in price_df.columns:
        # Map price_level to an average range
        price_level_map = {
            1: 150,  # $ = ~Rs. 150
            2: 300,  # $$ = ~Rs. 300
            3: 500,  # $$$ = ~Rs. 500
            4: 800   # $$$$ = ~Rs. 800
        }
        price_df['numeric_price'] = price_df['price_level'].map(price_level_map)
    
    # Drop rows without any price information
    price_df = price_df.dropna(subset=['numeric_price'])
    
    # Categorize items into common types
    if 'item_name' in price_df.columns:
        # Create a mapping for common coffee types
        coffee_type_mapping = {
            'americano': 'Americano',
            'espresso': 'Espresso',
            'cappuccino': 'Cappuccino',
            'latte': 'Latte',
            'mocha': 'Mocha',
            'macchiato': 'Macchiato',
            'flat white': 'Flat White',
            'cold brew': 'Cold Brew',
            'frappuccino': 'Frappuccino',
            'coffee': 'Regular Coffee',
        }
        
        # Apply mapping
        price_df['coffee_type'] = 'Other'
        for key, value in coffee_type_mapping.items():
            mask = price_df['item_name'].fillna('').str.lower().str.contains(key)
            price_df.loc[mask, 'coffee_type'] = value
    
    return price_df

def visualize_price_distribution(df):
    """
    Visualize the distribution of coffee prices.
    """
    if df is None or len(df) == 0:
        print("No data available for visualization.")
        return
    
    # Set up the plot
    plt.figure(figsize=(14, 8))
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create the histogram
    sns.histplot(data=df, x='numeric_price', bins=20, kde=True)
    plt.title('Distribution of Coffee Prices in Pakistan', fontsize=16)
    plt.xlabel('Price (PKR)', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Add statistics
    mean_price = df['numeric_price'].mean()
    median_price = df['numeric_price'].median()
    
    plt.axvline(mean_price, color='red', linestyle='--', alpha=0.8, label=f'Mean: Rs. {mean_price:.0f}')
    plt.axvline(median_price, color='green', linestyle='--', alpha=0.8, label=f'Median: Rs. {median_price:.0f}')
    plt.legend(fontsize=12)
    
    # Save the figure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, PATHS['reports'])
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(reports_dir, f"price_distribution_{timestamp}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    # Save latest version
    latest_file = os.path.join(reports_dir, "price_distribution_latest.png")
    plt.savefig(latest_file, dpi=300, bbox_inches='tight')
    
    print(f"Price distribution plot saved to: {output_file}")
    plt.close()

def visualize_price_by_city(df):
    """
    Visualize coffee prices by city.
    """
    if df is None or len(df) == 0 or 'location' not in df.columns:
        print("No location data available for visualization.")
        return
    
    # Extract city from location
    df['city'] = df['location'].str.split(',').str[0].str.strip()
    
    # Group by city
    city_prices = df.groupby('city')['numeric_price'].agg(['mean', 'median', 'std', 'count']).reset_index()
    city_prices = city_prices.sort_values('mean', ascending=False)
    
    # Filter to cities with enough data
    city_prices = city_prices[city_prices['count'] >= 3]
    
    # Set up the plot
    plt.figure(figsize=(16, 10))
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create the bar plot
    x = np.arange(len(city_prices))
    width = 0.4
    
    # Plot mean and median
    plt.bar(x - width/2, city_prices['mean'], width, label='Mean Price', color='#3498db', alpha=0.7)
    plt.bar(x + width/2, city_prices['median'], width, label='Median Price', color='#2ecc71', alpha=0.7)
    
    # Add error bars for standard deviation
    plt.errorbar(x - width/2, city_prices['mean'], yerr=city_prices['std'], fmt='none', capsize=5, color='#34495e', alpha=0.5)
    
    # Customize the plot
    plt.xlabel('City', fontsize=14)
    plt.ylabel('Price (PKR)', fontsize=14)
    plt.title('Coffee Prices by City in Pakistan', fontsize=16)
    plt.xticks(x, city_prices['city'], rotation=45, ha='right')
    plt.legend(fontsize=12)
    plt.grid(True, axis='y', alpha=0.3)
    
    # Add count annotations
    for i, count in enumerate(city_prices['count']):
        plt.annotate(f'n={count}', 
                    xy=(i, city_prices['mean'].iloc[i] + city_prices['std'].iloc[i] + 20),
                    ha='center', va='bottom',
                    fontsize=10)
    
    plt.tight_layout()
    
    # Save the figure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, PATHS['reports'])
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(reports_dir, f"price_by_city_{timestamp}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    # Save latest version
    latest_file = os.path.join(reports_dir, "price_by_city_latest.png")
    plt.savefig(latest_file, dpi=300, bbox_inches='tight')
    
    print(f"Price by city plot saved to: {output_file}")
    plt.close()

def visualize_price_by_coffee_type(df):
    """
    Visualize prices for different types of coffee.
    """
    if df is None or len(df) == 0 or 'coffee_type' not in df.columns:
        print("No coffee type data available for visualization.")
        return
    
    # Group by coffee type
    coffee_prices = df.groupby('coffee_type')['numeric_price'].agg(['mean', 'median', 'std', 'count']).reset_index()
    coffee_prices = coffee_prices[coffee_prices['count'] >= 2]  # Filter to types with at least 2 data points
    coffee_prices = coffee_prices.sort_values('mean', ascending=False)
    
    # Set up the plot
    plt.figure(figsize=(16, 10))
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create the bar plot
    x = np.arange(len(coffee_prices))
    width = 0.4
    
    # Plot mean and median
    plt.bar(x - width/2, coffee_prices['mean'], width, label='Mean Price', color='#e74c3c', alpha=0.7)
    plt.bar(x + width/2, coffee_prices['median'], width, label='Median Price', color='#f39c12', alpha=0.7)
    
    # Add error bars for standard deviation
    plt.errorbar(x - width/2, coffee_prices['mean'], yerr=coffee_prices['std'], fmt='none', capsize=5, color='#34495e', alpha=0.5)
    
    # Customize the plot
    plt.xlabel('Coffee Type', fontsize=14)
    plt.ylabel('Price (PKR)', fontsize=14)
    plt.title('Coffee Prices by Type in Pakistan', fontsize=16)
    plt.xticks(x, coffee_prices['coffee_type'], rotation=45, ha='right')
    plt.legend(fontsize=12)
    plt.grid(True, axis='y', alpha=0.3)
    
    # Add count annotations
    for i, count in enumerate(coffee_prices['count']):
        plt.annotate(f'n={count}', 
                    xy=(i, coffee_prices['mean'].iloc[i] + coffee_prices['std'].iloc[i] + 20),
                    ha='center', va='bottom',
                    fontsize=10)
    
    plt.tight_layout()
    
    # Save the figure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, PATHS['reports'])
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(reports_dir, f"price_by_coffee_type_{timestamp}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    # Save latest version
    latest_file = os.path.join(reports_dir, "price_by_coffee_type_latest.png")
    plt.savefig(latest_file, dpi=300, bbox_inches='tight')
    
    print(f"Price by coffee type plot saved to: {output_file}")
    plt.close()

def visualize_price_heatmap(df):
    """
    Create a heatmap showing coffee prices by city and type.
    """
    if df is None or len(df) == 0 or 'coffee_type' not in df.columns:
        print("No data available for heatmap visualization.")
        return
    
    # Extract city from location
    df['city'] = df['location'].str.split(',').str[0].str.strip()
    
    # Pivot table: cities as rows, coffee types as columns
    pivot = pd.pivot_table(df, 
                         values='numeric_price', 
                         index='city', 
                         columns='coffee_type', 
                         aggfunc='mean')
    
    # Filter to rows and columns with sufficient data
    pivot = pivot.loc[pivot.count(axis=1) >= 2]  # Keep cities with at least 2 coffee types
    pivot = pivot.loc[:, pivot.count() >= 2]  # Keep coffee types available in at least 2 cities
    
    if pivot.empty:
        print("Not enough data for heatmap visualization.")
        return
    
    # Set up the plot
    plt.figure(figsize=(16, 12))
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create the heatmap
    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlGnBu', linewidths=0.5)
    
    # Customize the plot
    plt.title('Coffee Prices (PKR) by City and Type', fontsize=16)
    plt.xlabel('Coffee Type', fontsize=14)
    plt.ylabel('City', fontsize=14)
    
    plt.tight_layout()
    
    # Save the figure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, PATHS['reports'])
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(reports_dir, f"price_heatmap_{timestamp}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    # Save latest version
    latest_file = os.path.join(reports_dir, "price_heatmap_latest.png")
    plt.savefig(latest_file, dpi=300, bbox_inches='tight')
    
    print(f"Price heatmap saved to: {output_file}")
    plt.close()

def generate_all_visualizations():
    """
    Generate all price visualization charts.
    """
    print("Generating coffee price visualizations...")
    
    # Load the data
    df = load_price_data()
    if df is None:
        print("No price data available. Run data collection and conversion first.")
        return
    
    # Preprocess the data
    processed_df = preprocess_price_data(df)
    if processed_df is None or len(processed_df) == 0:
        print("No valid price data available for visualization.")
        return
    
    print(f"Preprocessing complete. Found {len(processed_df)} valid price records.")
    
    # Generate each visualization
    visualize_price_distribution(processed_df)
    visualize_price_by_city(processed_df)
    visualize_price_by_coffee_type(processed_df)
    visualize_price_heatmap(processed_df)
    
    print("All visualizations complete!")

if __name__ == "__main__":
    print("Starting coffee price visualization...")
    generate_all_visualizations()
