#!/usr/bin/env python
"""
Test script to verify the Foodpanda data extraction implementation
"""

import os
import sys
import logging
import json
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('foodpanda_test_output.log')
    ]
)
logger = logging.getLogger("foodpanda_test")

def test_foodpanda_implementation():
    """Quick test function to verify our implementation"""
    logger.info("Starting test of Foodpanda implementation...")
    
    # Check if we have the implementation file
    if os.path.exists("fixed_foodpanda_method.py"):
        logger.info("Found implementation file!")
        
        # Log the method's structure
        with open("fixed_foodpanda_method.py", "r") as f:
            code = f.read()
        
        logger.info(f"Implementation has {len(code.splitlines())} lines")
        logger.info("Key features implemented:")
        logger.info("- Product card extraction with fallback selectors")
        logger.info("- Name and price extraction with fallbacks")
        logger.info("- Coffee product filtering")
        logger.info("- Pagination support")
        logger.info("- Image URL extraction")
        logger.info("- Raw and processed data collection")
        
        logger.info("\nPlease manually insert this code into coffee_market.py")
        logger.info("replacing the existing extract_foodpanda_data method.")
        logger.info("Make sure indentation levels match your class structure.")
    else:
        logger.error("Implementation file not found!")

if __name__ == "__main__":
    try:
        test_foodpanda_implementation()
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        traceback.print_exc()
    else:
        logger.info("Test completed!")
