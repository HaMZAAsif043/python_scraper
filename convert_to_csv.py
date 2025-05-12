import os
import json
import csv
import pandas as pd
from datetime import datetime
from src.config import PATHS

def convert_json_to_csv():
    """Convert the collected JSON data into CSV format with a focus on prices and traffic."""
    print("Converting JSON data to CSV format...")
    
    # Set paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_dir = os.path.join(base_dir, PATHS['raw_data'])
    processed_dir = os.path.join(base_dir, PATHS['processed_data'])
    
    # Create processed directory if it doesn't exist
    os.makedirs(processed_dir, exist_ok=True)
    
    # Get timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Load Google Maps data
    google_maps_data = []
    google_maps_file = os.path.join(raw_data_dir, "google_maps_latest.json")
    if os.path.exists(google_maps_file):
        try:
            with open(google_maps_file, 'r', encoding='utf-8') as f:
                google_maps_data = json.load(f)
                print(f"Loaded {len(google_maps_data)} records from Google Maps data")
        except Exception as e:
            print(f"Error loading Google Maps data: {e}")
    
    # Load Foursquare data
    foursquare_data = []
    foursquare_file = os.path.join(raw_data_dir, "foursquare_latest.json")
    if os.path.exists(foursquare_file):
        try:
            with open(foursquare_file, 'r', encoding='utf-8') as f:
                foursquare_data = json.load(f)
                print(f"Loaded {len(foursquare_data)} records from Foursquare data")
        except Exception as e:
            print(f"Error loading Foursquare data: {e}")
    
    # Process and combine the data
    combined_data = process_combined_data(google_maps_data, foursquare_data)
    
    # Create CSV files
    basic_csv_file = os.path.join(processed_dir, f"coffee_shops_basic_{timestamp}.csv")
    prices_csv_file = os.path.join(processed_dir, f"coffee_shops_prices_{timestamp}.csv")
    traffic_csv_file = os.path.join(processed_dir, f"coffee_shops_traffic_{timestamp}.csv")
    
    # Save to CSV files
    save_basic_data_csv(combined_data, basic_csv_file)
    save_price_data_csv(combined_data, prices_csv_file)
    save_traffic_data_csv(combined_data, traffic_csv_file)
    
    # Save latest versions
    save_basic_data_csv(combined_data, os.path.join(processed_dir, "coffee_shops_basic_latest.csv"))
    save_price_data_csv(combined_data, os.path.join(processed_dir, "coffee_shops_prices_latest.csv"))
    save_traffic_data_csv(combined_data, os.path.join(processed_dir, "coffee_shops_traffic_latest.csv"))
    
    print("Conversion completed!")
    return {
        "basic_csv": basic_csv_file,
        "prices_csv": prices_csv_file,
        "traffic_csv": traffic_csv_file
    }

def process_combined_data(google_maps_data, foursquare_data):
    """Process and combine data from both sources."""
    combined_data = []
    
    # Process Google Maps data
    for shop in google_maps_data:
        if not isinstance(shop, dict) or not shop.get("name"):
            continue
            
        shop_data = {
            "name": shop.get("name", ""),
            "location": shop.get("location", ""),
            "address": shop.get("address", ""),
            "source": "Google Maps",
            "rating": shop.get("rating"),
            "user_ratings_total": shop.get("user_ratings_total"),
            "price_level": shop.get("price_level"),
            "price_text": "$" * shop.get("price_level", 0) if shop.get("price_level") else "",
            "url": shop.get("url", ""),
            "latitude": None,
            "longitude": None,
            "collected_at": shop.get("collected_at", ""),
            "menu_items": []
        }
        
        # Extract coordinates if available
        if "location" in shop and isinstance(shop["location"], dict):
            shop_data["latitude"] = shop["location"].get("lat")
            shop_data["longitude"] = shop["location"].get("lng")
        
        # Extract popular times if available
        if "popular_times" in shop and isinstance(shop["popular_times"], dict):
            shop_data["popular_times"] = shop["popular_times"]
        
        # Extract menu items if available (typically not in Google Maps data)
        if "menu_items" in shop and isinstance(shop["menu_items"], list):
            shop_data["menu_items"] = shop["menu_items"]
        
        combined_data.append(shop_data)
    
    # Process Foursquare data
    for shop in foursquare_data:
        if not isinstance(shop, dict) or not shop.get("name"):
            continue
            
        shop_data = {
            "name": shop.get("name", ""),
            "location": shop.get("location", ""),
            "address": shop.get("address", ""),
            "source": "Foursquare",
            "rating": shop.get("rating"),
            "user_ratings_total": shop.get("user_ratings_total"),
            "price_level": shop.get("price_level"),
            "price_text": shop.get("price_text", ""),
            "category": shop.get("category", ""),
            "phone": shop.get("phone", ""),
            "website": shop.get("website", ""),
            "url": shop.get("url", ""),
            "collected_at": shop.get("collected_at", ""),
            "menu_items": shop.get("menu_items", [])
        }
        
        # Extract popular times if available
        if "popular_times" in shop and isinstance(shop["popular_times"], dict):
            shop_data["popular_times"] = shop["popular_times"]
        
        combined_data.append(shop_data)
    
    print(f"Combined {len(combined_data)} coffee shop records")
    return combined_data

def save_basic_data_csv(data, csv_file):
    """Save basic coffee shop information to a CSV file."""
    if not data:
        print("No data to save to basic CSV.")
        return
    
    columns = [
        "name", "source", "location", "address", "rating", "user_ratings_total",
        "price_level", "price_text", "category", "phone", "website", "url", "collected_at"
    ]
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for shop in data:
                row_data = {key: shop.get(key, "") for key in columns}
                writer.writerow(row_data)
        
        print(f"Basic CSV file saved: {csv_file}")
    except Exception as e:
        print(f"Error saving basic CSV file: {e}")

def save_price_data_csv(data, csv_file):
    """Save coffee shop price information to a CSV file."""
    if not data:
        print("No data to save to prices CSV.")
        return
    
    # Create a list to store the flattened price data
    price_rows = []
    
    for shop in data:
        # Basic shop info that will be repeated for each menu item
        shop_info = {
            "coffee_shop_name": shop.get("name", ""),
            "source": shop.get("source", ""),
            "location": shop.get("location", ""),
            "price_level": shop.get("price_level", ""),
            "price_text": shop.get("price_text", "")
        }
        
        # If there are menu items with prices, add them as separate rows
        menu_items = shop.get("menu_items", [])
        if menu_items:
            for item in menu_items:
                item_row = shop_info.copy()
                item_row.update({
                    "item_name": item.get("name", ""),
                    "item_price": item.get("price", ""),
                    "item_description": item.get("description", "")
                })
                price_rows.append(item_row)
        else:
            # If no menu items, just add the shop info as a row
            shop_info.update({
                "item_name": "",
                "item_price": "",
                "item_description": ""
            })
            price_rows.append(shop_info)
    
    # Define columns for the CSV
    price_columns = [
        "coffee_shop_name", "source", "location", "price_level", "price_text",
        "item_name", "item_price", "item_description"
    ]
    
    # Write to CSV
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=price_columns)
            writer.writeheader()
            writer.writerows(price_rows)
        
        print(f"Prices CSV file saved: {csv_file}")
    except Exception as e:
        print(f"Error saving prices CSV file: {e}")

def save_traffic_data_csv(data, csv_file):
    """Save coffee shop traffic/popular times information to a CSV file."""
    if not data:
        print("No data to save to traffic CSV.")
        return
    
    # Create a list to store the flattened traffic data
    traffic_rows = []
    
    for shop in data:
        # Check if there is popular times data
        popular_times = shop.get("popular_times", {})
        
        if popular_times and isinstance(popular_times, dict):
            for day, hours in popular_times.items():
                for hour_data in hours:
                    if isinstance(hour_data, dict):
                        hour = hour_data.get("hour")
                        popularity = hour_data.get("popularity", 0)
                        
                        # Skip entries with 0 popularity (usually means closed or no data)
                        if popularity > 0:
                            traffic_rows.append({
                                "coffee_shop_name": shop.get("name", ""),
                                "source": shop.get("source", ""),
                                "location": shop.get("location", ""),
                                "day_of_week": day,
                                "hour": hour,
                                "popularity_score": popularity
                            })
    
    # If no traffic data, create an empty CSV
    if not traffic_rows:
        print("No traffic data available.")
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["coffee_shop_name", "source", "location", "day_of_week", "hour", "popularity_score"])
        return
    
    # Define columns for the CSV
    traffic_columns = [
        "coffee_shop_name", "source", "location", "day_of_week", "hour", "popularity_score"
    ]
    
    # Write to CSV
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=traffic_columns)
            writer.writeheader()
            writer.writerows(traffic_rows)
        
        print(f"Traffic CSV file saved: {csv_file}")
    except Exception as e:
        print(f"Error saving traffic CSV file: {e}")

def create_price_comparison_excel():
    """Create an Excel file with price comparisons by city and coffee shop."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        processed_dir = os.path.join(base_dir, PATHS['processed_data'])
        
        # Load the price data CSV
        price_csv = os.path.join(processed_dir, "coffee_shops_prices_latest.csv")
        if not os.path.exists(price_csv):
            print("Price CSV file not found. Run conversion first.")
            return
        
        # Read the CSV into a pandas DataFrame
        df = pd.read_csv(price_csv)
        
        # Filter out rows without item prices
        price_df = df[df['item_price'].notna() & (df['item_price'] != '')]
        
        if len(price_df) == 0:
            print("No price data available for comparison.")
            return
            
        # Create an Excel writer
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = os.path.join(processed_dir, f"coffee_price_comparison_{timestamp}.xlsx")
        writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
        
        # Sheet 1: Overall price data
        price_df.to_excel(writer, sheet_name='All Price Data', index=False)
        
        # Sheet 2: Average prices by city
        try:
            # Convert item_price to numeric (strip currency symbols and convert)
            # This assumes prices are in the format "$XX.XX" or "XX.XX"
            price_df['numeric_price'] = price_df['item_price'].str.replace(r'[^\d.]', '', regex=True).astype(float)
            
            # Group by location and get average price
            city_prices = price_df.groupby('location')['numeric_price'].agg(['mean', 'min', 'max', 'count']).reset_index()
            city_prices.columns = ['City', 'Average Price', 'Minimum Price', 'Maximum Price', 'Number of Items']
            city_prices.to_excel(writer, sheet_name='Prices by City', index=False)
        except:
            print("Could not create city price analysis - price data may be inconsistent")
        
        # Sheet 3: Common coffee items price comparison
        try:
            # Filter for common coffee items (if they exist in the data)
            common_items = ['Espresso', 'Latte', 'Cappuccino', 'Americano', 'Coffee', 'Mocha']
            common_df = price_df[price_df['item_name'].str.contains('|'.join(common_items), case=False, na=False)]
            
            if len(common_df) > 0:
                # Create pivot table with cities as rows and coffee types as columns
                pivot = pd.pivot_table(common_df, 
                                      values='numeric_price', 
                                      index='location', 
                                      columns='item_name', 
                                      aggfunc='mean')
                
                pivot.to_excel(writer, sheet_name='Common Coffee Prices')
        except:
            print("Could not create common coffee items analysis")
        
        # Save the Excel file
        writer.close()
        print(f"Price comparison Excel file created: {excel_file}")
        
        # Copy as latest version
        latest_excel = os.path.join(processed_dir, "coffee_price_comparison_latest.xlsx")
        import shutil
        shutil.copy2(excel_file, latest_excel)
        
        return excel_file
    
    except Exception as e:
        print(f"Error creating Excel price comparison: {e}")
        return None

if __name__ == "__main__":
    print("Converting coffee shop data to CSV format...")
    convert_json_to_csv()
    
    print("\nCreating price comparison Excel file...")
    create_price_comparison_excel()
    
    print("\nConversion complete!")
