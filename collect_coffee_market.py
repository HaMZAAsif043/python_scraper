#!/usr/bin/env python
"""
Script to collect coffee market data from Pakistan e-commerce websites.

This script extracts publicly available data on coffee products sold in Pakistan,
focusing on:
- Types of coffee (instant, ground, beans, powdered)
- Packaging sizes and variants
- Price data and segmentation
- Customer reviews and ratings
- Brand popularity and market presence

Data is collected from popular Pakistani e-commerce websites without using any API keys.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the coffee market data collector
from src.data_collection.coffee_market import collect_coffee_market_data

def main():
    """
    Main function to run the coffee market data collection.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("coffee_market_collection.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting coffee market data collection")
    
    # Start time for performance tracking
    start_time = datetime.now()
    logger.info(f"Collection started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run the data collection
        result = collect_coffee_market_data()
        
        # Summarize results
        products_count = len(result['data']['products'])
        brands_count = len(result['data']['brands'])
        coffee_types = ', '.join(result['data']['types'].keys())
        
        logger.info(f"Data collection completed successfully")
        logger.info(f"Collected data for {products_count} products from {brands_count} brands")
        logger.info(f"Coffee types identified: {coffee_types}")
        
        # Print file paths
        logger.info("Data saved to the following files:")
        for file_type, path in result['saved_paths'].items():
            if isinstance(path, dict):  # For CSV files dictionary
                for sub_type, sub_path in path.items():
                    logger.info(f"- {file_type} ({sub_type}): {sub_path}")
            else:
                logger.info(f"- {file_type}: {path}")
                
        # End time and duration
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Collection finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total duration: {duration}")
        
        # Print summary to console
        print("\nCoffee Market Data Collection Summary")
        print("===================================")
        print(f"Total Products: {products_count}")
        print(f"Total Brands: {brands_count}")
        print(f"Coffee Types: {coffee_types}")
        
        # Show price tier distribution
        low_tier = len(result['data']['price_tiers']['low'])
        mid_tier = len(result['data']['price_tiers']['mid'])
        premium_tier = len(result['data']['price_tiers']['premium'])
        print("\nPrice Tier Distribution:")
        print(f"- Economy (< Rs.1,000): {low_tier} products")
        print(f"- Mid-range (Rs.1,001-2,500): {mid_tier} products")
        print(f"- Premium (> Rs.2,500): {premium_tier} products")
        
        # Display data locations
        print("\nData files available at:")
        print(f"- Raw JSON: {result['saved_paths']['raw_json']}")
        print(f"- Products CSV: {result['saved_paths']['csv_files']['products']}")
        print(f"- Brands CSV: {result['saved_paths']['csv_files']['brands']}")
        
        # Return success code
        return 0
        
    except Exception as e:
        logger.error(f"Error during coffee market data collection: {e}", exc_info=True)
        print(f"\nERROR: Data collection failed - {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
