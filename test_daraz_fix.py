"""
Test script to verify just the Daraz price extraction fix.
"""

import logging
import os
import sys
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"daraz_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.abspath('src'))

def test_daraz_price_extraction_only():
    """Test just the improved Daraz price extraction with a single page"""
    from src.data_collection.coffee_market import CoffeeMarketDataCollector
    
    logger.info("Testing Daraz price extraction...")
    
    # Create collector instance with cache enabled to speed up testing
    collector = CoffeeMarketDataCollector(use_cache=True, cache_duration_hours=24)
    
    # Only test 1 page to keep the test quick
    max_pages = 1
    
    # Extract Daraz data for just one page
    collector.extract_daraz_data(max_pages=max_pages)
    
    # Check if products were extracted
    products = [p for p in collector.processed_data['products'] if p['source'] == 'daraz.pk']
    logger.info(f"Extracted {len(products)} products from Daraz")
    
    # Save the extracted products for inspection
    with open("daraz_extracted_products.json", "w") as f:
        json.dump(products, f, indent=2)
    logger.info("Saved products to daraz_extracted_products.json")
    
    # Check if prices were extracted correctly (non-zero prices)
    valid_prices = [p for p in products if p['price'] > 0]
    logger.info(f"Products with valid prices: {len(valid_prices)}/{len(products)}")
    
    # Log first 5 products for manual inspection
    logger.info("First 5 products with prices:")
    for i, product in enumerate(products[:5]):
        logger.info(f"{i+1}. {product['name']} - Price: {product['price']}")
    
    # Calculate percentage of successful price extraction
    price_success_rate = len(valid_prices) / len(products) * 100 if products else 0
    logger.info(f"Price extraction success rate: {price_success_rate:.2f}%")
    
    return price_success_rate >= 80  # Consider success if at least 80% of prices were extracted

if __name__ == "__main__":
    logger.info("Starting Daraz price extraction test...")
    success = test_daraz_price_extraction_only()
    if success:
        print("SUCCESS: Daraz price extraction is working correctly!")
    else:
        print("FAILURE: Daraz price extraction still has issues.")
