"""
Test script for the extract_foodpanda_data method
"""

import logging
import sys
from src.data_collection.coffee_market import CoffeeMarketDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('foodpanda_test.log')
    ]
)

def main():
    print("Starting Foodpanda data extraction test...")
    collector = CoffeeMarketDataCollector(use_cache=False)
    
    # Extract data from Foodpanda only
    collector.extract_foodpanda_data(max_pages=2)
    
    # Print results
    print("\nExtraction Results:")
    print(f"Total products collected: {len(collector.processed_data['products'])}")
    
    # Show first 5 products
    print("\nSample Products:")
    for i, product in enumerate(collector.processed_data['products'][:5]):
        print(f"\nProduct {i+1}:")
        print(f"  Name: {product['name']}")
        print(f"  Price: {product['price']}")
        print(f"  Brand: {product['brand']}")
        print(f"  Type: {product['type']}")
        print(f"  Image URL: {product['image_url'][:60]}..." if product['image_url'] else "  Image URL: None")

if __name__ == "__main__":
    main()
