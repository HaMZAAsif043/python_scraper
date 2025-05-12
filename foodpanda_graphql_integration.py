"""
Integration module to connect the Foodpanda GraphQL extractor 
with the main coffee market data collector system.

This module provides functions to extract Pandamart coffee product data
using the GraphQL API across multiple cities in Pakistan.
"""

import os
import asyncio
import json
import logging
import time
from datetime import datetime

# Import the GraphQL extractor
from foodpanda_graphql_extractor import FoodpandaGraphQLExtractor

logger = logging.getLogger(__name__)

async def extract_foodpanda_graphql_data(max_cities=None, headless=True):
    """
    Extract coffee product data from Pandamart vendors across Pakistan using GraphQL API.
    
    Args:
        max_cities (int): Maximum number of cities to process (None for all)
        headless (bool): Whether to run the browser in headless mode
        
    Returns:
        list: Extracted coffee product data
    """
    logger.info("Starting extraction of coffee data from Foodpanda using GraphQL API")
    
    start_time = time.time()
    
    # Create the extractor instance
    extractor = FoodpandaGraphQLExtractor(headless=headless)
    
    # Discover Pandamart vendors across cities
    vendor_ids = await extractor.discover_pandamart_vendors()
    
    if not vendor_ids:
        logger.warning("No Pandamart vendors found")
        return []
    
    # Limit the number of cities if specified
    cities = list(vendor_ids.keys())
    if max_cities and max_cities < len(cities):
        logger.info(f"Limiting to {max_cities} cities out of {len(cities)}")
        cities = cities[:max_cities]
    
    # Extract data for each vendor
    all_coffee_data = []
    for city in cities:
        vendor_id = vendor_ids[city]
        coffee_data = extractor.fetch_coffee_products_via_graphql(vendor_id, city)
        if coffee_data:
            all_coffee_data.append(coffee_data)
        # Wait between requests to avoid rate limiting
        time.sleep(1)
    
    # Transform to standard format
    standard_products = extractor.transform_to_standard_format(all_coffee_data)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Extracted {len(standard_products)} coffee products from {len(all_coffee_data)} cities via GraphQL API in {elapsed_time:.2f} seconds")
    
    # Save data if needed (optional)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = extractor.save_data(standard_products, timestamp)
    logger.info(f"Saved GraphQL data to {output_file}")
    
    return standard_products

def get_graphql_products_for_coffee_market():
    """
    Function to be called from the main coffee market data collector.
    Returns standardized coffee product data from Pandamart GraphQL API.
    """
    try:
        # Run the async extraction function
        loop = asyncio.get_event_loop()
        products = loop.run_until_complete(extract_foodpanda_graphql_data(headless=True))
        return products
    except Exception as e:
        logger.error(f"Error extracting Foodpanda GraphQL data: {e}")
        return []

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("foodpanda_graphql.log"),
            logging.StreamHandler()
        ]
    )
    
    # Test the extraction function directly
    loop = asyncio.get_event_loop()
    products = loop.run_until_complete(extract_foodpanda_graphql_data(
        max_cities=5,  # Limit to 5 cities for testing
        headless=False  # Show browser UI for debugging
    ))
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"Total products: {len(products)}")
    
    # Group by city
    cities = {}
    for product in products:
        city = product.get("city", "Unknown")
        cities[city] = cities.get(city, 0) + 1
    
    print("\nProducts by city:")
    for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
        print(f"  {city}: {count}")
    
    # Group by brand
    brands = {}
    for product in products:
        brand = product.get("brand", "Unknown")
        brands[brand] = brands.get(brand, 0) + 1
    
    print("\nProducts by brand:")
    for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
        print(f"  {brand}: {count}")
    
    # Group by coffee type
    types = {}
    for product in products:
        coffee_type = product.get("type", "Unknown")
        types[coffee_type] = types.get(coffee_type, 0) + 1
    
    print("\nProducts by type:")
    for coffee_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {coffee_type}: {count}")
