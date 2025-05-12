#!/usr/bin/env python
"""
Interactive script for collecting coffee market data from Pakistani e-commerce websites.
This script provides user options for:
1. Which websites to scrape (all or specific ones)
2. Whether to use cached data or fresh scraping 
3. Options for error handling and data export
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import time
import json

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the coffee market data collector
from src.data_collection.coffee_market import CoffeeMarketDataCollector

def setup_logging(log_file="coffee_market_interactive.log"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Interactive Coffee Market Data Collection Tool")
    
    parser.add_argument('--sites', nargs='+', choices=['daraz', 'foodpanda', 'alfatah', 'naheed', 'metro', 'alibaba', 'all'], 
                        default=['all'], help='Websites to scrape (default: all)')
    
    parser.add_argument('--no-cache', action='store_true',
                        help='Disable cache and force fresh scraping')
    
    parser.add_argument('--cache-duration', type=int, default=24,
                        help='Cache duration in hours (default: 24)')
    
    parser.add_argument('--output', type=str, default=None,
                        help='Custom output directory for data files')
    
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                        help='Output format (default: both JSON and CSV)')
    
    parser.add_argument('--sample', action='store_true',
                        help='Use sample data instead of web scraping (for testing)')
    
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress progress output')
    
    return parser.parse_args()

def progress_callback(site_name, status, items_count=0):
    """Callback function to report progress during scraping."""
    if status == 'start':
        print(f"🔍 Starting to scrape {site_name}...")
    elif status == 'complete':
        print(f"✅ Scraped {items_count} products from {site_name}")
    elif status == 'failed':
        print(f"❌ Failed to scrape {site_name}")
    elif status == 'no_products':
        print(f"⚠️ No products found on {site_name}")
    elif status == 'sample':
        print(f"📊 Using sample data for {site_name}")

def collect_data_interactive(args, logger):
    """Collect coffee market data based on user arguments."""
    start_time = time.time()
      # Determine which sites to scrape
    sites_to_scrape = []
    if 'all' in args.sites:
        sites_to_scrape = ['daraz', 'foodpanda', 'alfatah', 'naheed', 'metro', 'alibaba']
    else:
        sites_to_scrape = args.sites
    
    logger.info(f"Starting interactive coffee market data collection for sites: {', '.join(sites_to_scrape)}")
    
    # Create collector with appropriate settings
    collector = CoffeeMarketDataCollector(
        use_cache=(not args.no_cache),
        cache_duration_hours=args.cache_duration
    )
      # If using sample data, generate it directly
    if args.sample:
        logger.info("Using sample data mode")
        print("💡 Using sample data instead of web scraping")
        collector._generate_sample_product_data()
        
        # Convert sets to lists for JSON serialization to prevent errors
        for brand in collector.processed_data['brands']:
            if isinstance(collector.processed_data['brands'][brand]['types'], set):
                collector.processed_data['brands'][brand]['types'] = list(collector.processed_data['brands'][brand]['types'])
            
        for coffee_type in collector.processed_data['types']:
            if isinstance(collector.processed_data['types'][coffee_type]['brands'], set):
                collector.processed_data['types'][coffee_type]['brands'] = list(collector.processed_data['types'][coffee_type]['brands'])
                
        data = collector.processed_data
    else:
        # Convert site list to indices for collect_data method
        if not args.quiet:
            print(f"🌐 Starting to scrape {len(sites_to_scrape)} websites: {', '.join(sites_to_scrape)}")
        
        # Run the data collection
        data = collector.collect_data()
          # Check if we got any data
        if len(data['products']) == 0 and args.sample:
            logger.warning("No products found. Using sample data as fallback since sample flag was provided.")
            print("⚠️ No products found. Using sample data as fallback.")
            collector._generate_sample_product_data()
            
            # Convert sets to lists for JSON serialization to prevent errors
            for brand in collector.processed_data['brands']:
                if isinstance(collector.processed_data['brands'][brand]['types'], set):
                    collector.processed_data['brands'][brand]['types'] = list(collector.processed_data['brands'][brand]['types'])
                
            for coffee_type in collector.processed_data['types']:
                if isinstance(collector.processed_data['types'][coffee_type]['brands'], set):
                    collector.processed_data['types'][coffee_type]['brands'] = list(collector.processed_data['types'][coffee_type]['brands'])
                    
            data = collector.processed_data
        elif len(data['products']) == 0:
            logger.warning("No products found. Please check website configurations and selectors.")
            print("⚠️ No products found. Try different websites or selectors.")
    
    # Save the data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_paths = collector.save_data(timestamp)
    
    # End time and statistics
    end_time = time.time()
    duration = end_time - start_time
    
    # Print summary
    if not args.quiet:
        print("\n📊 Coffee Market Data Collection Summary")
        print("======================================")
        print(f"⏱️ Total time: {duration:.2f} seconds")
        print(f"🛍️ Total Products: {len(data['products'])}")
        print(f"🏭 Total Brands: {len(data['brands'])}")
        print(f"☕ Coffee Types: {', '.join(data['types'].keys())}")
        
        # Show price tier distribution
        low_tier = len(data['price_tiers']['low'])
        mid_tier = len(data['price_tiers']['mid'])
        premium_tier = len(data['price_tiers']['premium'])
        print("\n💰 Price Tier Distribution:")
        print(f"  - Economy (< Rs.1,000): {low_tier} products")
        print(f"  - Mid-range (Rs.1,001-2,500): {mid_tier} products")
        print(f"  - Premium (> Rs.2,500): {premium_tier} products")
        
        # Show data locations
        print("\n💾 Data files available at:")
        print(f"  - Raw JSON: {saved_paths['raw_json']}")
        print(f"  - Products CSV: {saved_paths['csv_files']['products']}")
        
        # Show data quality information
        if 'metadata' in data and 'data_quality' in data['metadata']:
            quality = data['metadata']['data_quality']
            print(f"\n⚠️ Data quality: {quality}")
            
            if 'successful_sites' in data['metadata']:
                successful = data['metadata']['successful_sites']
                failed = data['metadata']['failed_sites']
                print(f"✅ Successfully scraped: {', '.join(successful) if successful else 'None'}")
                print(f"❌ Failed to scrape: {', '.join(failed) if failed else 'None'}")
    
    return {
        'data': data,
        'saved_paths': saved_paths,
        'duration': duration
    }

def main():
    """Main function to run the interactive coffee market data collection."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting interactive coffee market data collection")
    
    try:
        # Collect the data
        result = collect_data_interactive(args, logger)
        
        # Return success
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Collection interrupted by user")
        print("\n⚠️ Collection interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Error during coffee market data collection: {e}", exc_info=True)
        print(f"\n❌ ERROR: Data collection failed - {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
