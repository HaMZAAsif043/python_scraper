#!/usr/bin/env python
"""
Simplified test script for Foodpanda coffee data extraction
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the coffee market data collector
from src.data_collection.coffee_market import CoffeeMarketDataCollector

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("foodpanda_test.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main function for testing Foodpanda data extraction."""
    logger = setup_logging()
    logger.info("Starting Foodpanda data extraction test")
    
    # Create the collector
    collector = CoffeeMarketDataCollector(use_cache=False)
    
    try:
        # Extract data from Foodpanda
        collector.extract_foodpanda_data(max_pages=2)
        
        # Print basic stats
        products = collector.processed_data.get('products', [])
        logger.info(f"Total products extracted: {len(products)}")
        
        # Print sample data
        if products:
            logger.info("Sample product data:")
            for i, product in enumerate(products[:3]):
                logger.info(f"Product {i+1}:")
                logger.info(f"  Name: {product.get('name', 'Unknown')}")
                logger.info(f"  Price: {product.get('price', 0)}")
                logger.info(f"  Brand: {product.get('brand', 'Unknown')}")
        else:
            logger.warning("No products were extracted")
            
        # Save data to file for inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"foodpanda_test_results_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collector.processed_data, f, indent=2)
        logger.info(f"Saved results to {output_file}")
        
    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)

if __name__ == "__main__":
    main()
