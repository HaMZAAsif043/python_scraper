#!/usr/bin/env python
"""
Test script to run only the Foodpanda extraction to check if the implementation works
"""

import os
import sys
import logging
import json
from datetime import datetime
import traceback
import time
import re
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('foodpanda_only_test.log')
    ]
)
logger = logging.getLogger("foodpanda_test")

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the coffee market module using importlib to avoid potential __init__.py issues
try:
    from src.data_collection.coffee_market import CoffeeMarketDataCollector
    logger.info("Successfully imported CoffeeMarketDataCollector directly")
except Exception as e:
    logger.error(f"Error importing directly: {e}")
    try:
        # Alternative import using importlib
        spec = importlib.util.spec_from_file_location(
            "coffee_market", 
            os.path.join("src", "data_collection", "coffee_market.py")
        )
        coffee_market = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(coffee_market)
        CoffeeMarketDataCollector = coffee_market.CoffeeMarketDataCollector
        logger.info("Successfully imported CoffeeMarketDataCollector using importlib")
    except Exception as e:
        logger.error(f"Error importing with importlib: {e}")
        sys.exit(1)

def verify_implementation():
    """Check if the _is_coffee_product method exists"""
    collector = CoffeeMarketDataCollector()
    
    if hasattr(collector, '_is_coffee_product'):
        logger.info("_is_coffee_product method found!")
    else:
        logger.warning("_is_coffee_product method NOT found! Will add it.")
        
        # Temporarily add the _is_coffee_product method to the instance
        def _is_coffee_product(self, product_name):
            """
            Check if a product is coffee-related based on its name.
            """
            if not product_name or product_name == "Unknown":
                return False
                
            # Convert to lowercase for case-insensitive matching
            name_lower = product_name.lower()
            
            # Coffee-related keywords
            coffee_keywords = [
                'coffee', 'café', 'caffè', 'kaffee', 'nescafe', 'espresso', 'cappuccino', 
                'latte', 'mocha', 'americano', 'java', 'brew', 'arabica', 'robusta', 
                'decaf', 'coffeehouse', 'coffeeshop', 'kopi', 'kahwa'
            ]
            
            # Check if any coffee keyword is in product name
            for keyword in coffee_keywords:
                if keyword in name_lower:
                    return True
                    
            return False
            
        # Bind the method to the instance
        collector._is_coffee_product = _is_coffee_product.__get__(collector, CoffeeMarketDataCollector)
    
    return collector

def test_foodpanda_extraction():
    """Main test function to run Foodpanda extraction"""
    logger.info("Starting Foodpanda extraction test")
    
    # Get collector instance with verification
    collector = verify_implementation()
    
    try:
        # Run the extraction with just 2 pages for testing
        logger.info("Extracting data from Foodpanda (max 2 pages)")
        collector.extract_foodpanda_data(max_pages=2)
        
        # Check results
        products = collector.processed_data.get('products', [])
        
        logger.info(f"Successfully extracted {len(products)} products")
        
        if products:
            # Save results to file for inspection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"foodpanda_results_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                # Extract first 5 products or all if fewer
                sample_products = products[:min(5, len(products))]
                json.dump(sample_products, f, indent=2)
            logger.info(f"Saved sample results to {output_file}")
            
            # Show sample output
            logger.info("\nSample Products:")
            for i, product in enumerate(sample_products):
                logger.info(f"\nProduct {i+1}:")
                logger.info(f"  Name: {product.get('name', 'Unknown')}")
                logger.info(f"  Price: {product.get('price', 0)}")
                logger.info(f"  Brand: {product.get('brand', 'Unknown')}")
                logger.info(f"  Type: {product.get('type', 'Unknown')}")
                logger.info(f"  Image URL: {product.get('image_url', 'None')[:50]}..." if product.get('image_url') else "  Image URL: None")
                
                # Check for empty or None values
                empty_fields = [field for field, value in product.items() 
                                if value is None or (isinstance(value, str) and value.strip() == "")]
                if empty_fields:
                    logger.warning(f"  Empty fields: {', '.join(empty_fields)}")
        else:
            logger.warning("No products were extracted from Foodpanda!")
    
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_foodpanda_extraction()
