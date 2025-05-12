"""
Test script to verify the fixes made to the coffee market data collector.
This script tests:
1. Daraz price extraction and pagination
2. Alfatah infinite scrolling
"""

import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"coffee_fixes_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.abspath('src'))

def test_daraz_price_extraction():
    """Test the improved Daraz price extraction and pagination"""
    from src.data_collection.coffee_market import CoffeeMarketDataCollector
    
    logger.info("Testing Daraz price extraction and pagination...")
    
    # Create collector instance with a small cache duration for testing
    collector = CoffeeMarketDataCollector(cache_duration_hours=0.1)
    
    # Only test 3 pages to keep the test quick
    max_pages = 3
    
    # Extract Daraz data
    collector.extract_daraz_data(max_pages=max_pages)
    
    # Check if products were extracted
    products = [p for p in collector.processed_data['products'] if p['source'] == 'daraz.pk']
    logger.info(f"Extracted {len(products)} products from Daraz")
    
    # Check if prices were extracted correctly (non-zero prices)
    valid_prices = [p for p in products if p['price'] > 0]
    logger.info(f"Products with valid prices: {len(valid_prices)}/{len(products)}")
    
    # Calculate percentage of successful price extraction
    price_success_rate = len(valid_prices) / len(products) * 100 if products else 0
    logger.info(f"Price extraction success rate: {price_success_rate:.2f}%")
    
    return price_success_rate >= 80  # Consider success if at least 80% of prices were extracted

def test_alfatah_infinite_scroll():
    """Test the Alfatah infinite scrolling implementation"""
    from src.data_collection.coffee_market import CoffeeMarketDataCollector
    
    logger.info("Testing Alfatah infinite scrolling...")
    
    # Create collector instance with a small cache duration for testing
    collector = CoffeeMarketDataCollector(cache_duration_hours=0.1)
    
    # Only test 2 scroll iterations to keep the test quick
    max_scrolls = 2
    
    # Extract Alfatah data with infinite scrolling
    collector.extract_alfatah_data_with_infinite_scroll(max_pages=max_scrolls)
    
    # Check if products were extracted
    products = [p for p in collector.processed_data['products'] if p['source'] == 'alfatah.pk']
    logger.info(f"Extracted {len(products)} products from Alfatah with infinite scrolling")
    
    # The test is successful if we got any products
    return len(products) > 0

def run_tests():
    """Run all tests"""
    results = {
        "daraz_price_extraction": test_daraz_price_extraction(),
        "alfatah_infinite_scroll": test_alfatah_infinite_scroll()
    }
    
    logger.info("===== TEST RESULTS =====")
    all_passed = True
    for test, passed in results.items():
        result = "PASSED" if passed else "FAILED"
        logger.info(f"{test}: {result}")
        all_passed = all_passed and passed
    
    logger.info("===== SUMMARY =====")
    logger.info(f"All tests passed: {all_passed}")
    
    return all_passed

if __name__ == "__main__":
    logger.info("Starting tests for coffee market data collector fixes...")
    run_tests()
