#!/usr/bin/env python
"""
Script to test the Foodpanda GraphQL extraction for coffee products.
This script runs the GraphQL extractor in standalone mode without 
needing to run the full coffee market data collector.
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("foodpanda_graphql_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the GraphQL extractor
from foodpanda_graphql_extractor import FoodpandaGraphQLExtractor

async def main():
    print("\n🚀 FOODPANDA GRAPHQL COFFEE PRODUCT EXTRACTOR")
    print("===========================================\n")    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Extract coffee product data from Foodpanda using GraphQL API')
    parser.add_argument('--cities', type=int, default=5, help='Maximum number of cities to process')
    parser.add_argument('--show-browser', dest='headless', action='store_false',
                       help='Show browser UI during extraction (non-headless mode)')
    parser.add_argument('--headless', dest='headless', action='store_true',
                       help='Run in headless mode (no browser UI)')
    parser.add_argument('--output', type=str, default=None, help='Custom output file path')
    parser.set_defaults(headless=False)
    args = parser.parse_args()
    
    print(f"Configuration:")
    print(f"- Max cities: {args.cities}")
    print(f"- Headless mode: {args.headless}")
    print(f"- Output: {'Custom' if args.output else 'Default'}")
    print()
    
    # Create the extractor
    extractor = FoodpandaGraphQLExtractor(headless=args.headless)
    
    # Start the extraction process
    print("Step 1: Discovering Pandamart vendors across cities...\n")
    
    # Discover vendors
    vendor_ids = await extractor.discover_pandamart_vendors()
      # Check if any vendors were found
    if not vendor_ids:
        print("⚠️ No Pandamart vendors found automatically. Using fallback vendor IDs...")
        # Fallback vendor IDs for major cities
        vendor_ids = {
            "Karachi": "dp9i",
            "Lahore": "m1ba",
            "Islamabad": "w6mx",
            "Rawalpindi": "gb88",
            "Faisalabad": "v1mv"
        }
        print("✅ Using fallback vendor IDs for testing")
    
    # Print vendor IDs
    print(f"\n✅ Found {len(vendor_ids)} Pandamart vendors:")
    for city, vendor_id in vendor_ids.items():
        print(f"  • {city}: {vendor_id}")
    
    # Limit the number of cities if specified
    cities = list(vendor_ids.keys())
    if args.cities and args.cities < len(cities):
        print(f"\nLimiting to {args.cities} cities out of {len(cities)}")
        cities = cities[:args.cities]
    
    # Extract data for each vendor
    print("\nStep 2: Extracting coffee products from each vendor...\n")
    
    all_coffee_data = []
    for city in cities:
        vendor_id = vendor_ids[city]
        print(f"Processing {city} (vendor: {vendor_id})...")
        coffee_data = extractor.fetch_coffee_products_via_graphql(vendor_id, city)
        if coffee_data:
            product_count = len(coffee_data.get("products", []))
            print(f"  ✅ Found {product_count} coffee products")
            all_coffee_data.append(coffee_data)
        else:
            print(f"  ❌ No coffee products found")
    
    # Transform to standard format
    print("\nStep 3: Transforming data to standard format...\n")
    standard_products = extractor.transform_to_standard_format(all_coffee_data)
    
    # Save data
    print("\nStep 4: Saving extracted data...\n")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.output:
        output_file = args.output
    else:
        output_file = os.path.join("data", "raw", f"foodpanda_graphql_results_{timestamp}.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(standard_products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(standard_products)} products to {output_file}")
    
    # Print summary
    print("\n📊 SUMMARY:")
    print(f"Total products: {len(standard_products)}")
    
    # Group by city
    cities = {}
    for product in standard_products:
        city = product.get("city", "Unknown")
        cities[city] = cities.get(city, 0) + 1
    
    print("\nProducts by city:")
    for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
        print(f"  {city}: {count}")
    
    # Group by brand
    brands = {}
    for product in standard_products:
        brand = product.get("brand", "Unknown")
        brands[brand] = brands.get(brand, 0) + 1
    
    print("\nProducts by brand:")
    for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]:  # Show top 10
        print(f"  {brand}: {count}")
    
    # Group by coffee type
    types = {}
    for product in standard_products:
        coffee_type = product.get("type", "Unknown")
        types[coffee_type] = types.get(coffee_type, 0) + 1
    
    print("\nProducts by type:")
    for coffee_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {coffee_type}: {count}")
    
    # Group by price tier
    price_tiers = {}
    for product in standard_products:
        tier = product.get("price_tier", "Unknown")
        price_tiers[tier] = price_tiers.get(tier, 0) + 1
    
    print("\nProducts by price tier:")
    for tier, count in sorted(price_tiers.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tier}: {count}")
    
    print("\n✨ Extraction completed successfully!")

if __name__ == "__main__":
    # Ensure the output directory exists
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    
    # Run the main function
    asyncio.run(main())
