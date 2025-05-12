"""
Integration script to add the Foodpanda GraphQL extractor to the coffee_market.py file.

This script should be run to modify the coffee_market.py file to include the GraphQL 
extraction functionality. It will add a new method to the CoffeeMarketDataCollector class.

WARNING: Make sure to create a backup of your coffee_market.py file before running this script.
"""

import os
import re
import shutil
import logging
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Function to be added to coffee_market.py
FOODPANDA_GRAPHQL_METHOD = """    def extract_foodpanda_graphql_data(self, max_cities=5):
        \"\"\"
        Extract coffee product data from Pandamart vendors across Pakistan using GraphQL API.
        
        Args:
            max_cities (int): Maximum number of cities to process
            
        Returns:
            list: Extracted coffee product data
        \"\"\"
        try:
            # Import the GraphQL integration module
            from foodpanda_graphql_integration import extract_foodpanda_graphql_data
            import asyncio
            
            logger.info("Extracting coffee data from Foodpanda using GraphQL API")
            start_time = datetime.now()
            
            # Create/get event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # If there's no event loop in this thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Run the async extraction function
            products = loop.run_until_complete(extract_foodpanda_graphql_data(
                max_cities=max_cities,
                headless=True  # Use headless mode in production
            ))
            
            # Process the extracted products
            if products:
                logger.info(f"Successfully extracted {len(products)} products using GraphQL API")
                
                # Add to raw data collection
                for product in products:
                    # Add each product to the raw data collection
                    self.raw_data.append(product)
                    
                    # Add to processed categories
                    self.processed_data['products'].append(product)
                    
                    # Update aggregated data
                    self._update_aggregated_data(product)
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Extracted {len(products)} products from Foodpanda GraphQL in {elapsed_time:.2f} seconds")
                return products
            else:
                logger.warning("No products extracted from Foodpanda GraphQL API")
                return []
                
        except ImportError:
            logger.warning("Foodpanda GraphQL integration module not found. Skipping GraphQL extraction.")
            return []
        except Exception as e:
            logger.error(f"Error extracting data from Foodpanda GraphQL API: {e}")
            return []
"""

# Function call to be added to collect_data method
COLLECT_DATA_UPDATE = """        # Extract data from each target website
        for site in self.target_websites.keys():
            try:
                if site == 'foodpanda':
                    # Use GraphQL API extraction for better coverage
                    graphql_products = self.extract_foodpanda_graphql_data(max_cities=5)
                    if graphql_products:
                        logger.info(f"Used GraphQL API to extract {len(graphql_products)} products from {site}")
                        continue
                    else:
                        logger.warning(f"GraphQL extraction failed, falling back to standard method for {site}")
                        
                # Standard extraction method
                start_time = datetime.now()
                extract_method = getattr(self, f"extract_{site}_data", None)
                if extract_method:
                    extract_method()
"""

def backup_file(file_path):
    """Create a backup of the file"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False

def integrate_graphql_extractor():
    """Integrate the GraphQL extractor into coffee_market.py"""
    coffee_market_path = os.path.join("src", "data_collection", "coffee_market.py")
    
    # Check if the file exists
    if not os.path.exists(coffee_market_path):
        logger.error(f"File not found: {coffee_market_path}")
        return False
    
    # Create a backup
    if not backup_file(coffee_market_path):
        logger.error("Aborting due to backup failure")
        return False
    
    # Read the file content
    with open(coffee_market_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Add the GraphQL method to the CoffeeMarketDataCollector class
    # Look for the end of the last method in the class
    class_methods_pattern = r'(class CoffeeMarketDataCollector.*?)(def collect_data_for_category|def collect_data)'
    match = re.search(class_methods_pattern, content, re.DOTALL)
    
    if not match:
        logger.error("Could not find the CoffeeMarketDataCollector class definition")
        return False
    
    # Insert the new method before collect_data or collect_data_for_category
    class_def_with_methods = match.group(1)
    next_method_def = match.group(2)
    
    # Check if the method already exists
    if 'def extract_foodpanda_graphql_data' in content:
        logger.info("GraphQL method already exists in coffee_market.py")
    else:
        # Add the new method
        updated_class = class_def_with_methods + FOODPANDA_GRAPHQL_METHOD + "\n    " + next_method_def
        content = content.replace(match.group(0), updated_class)
    
    # Update the collect_data method
    collect_data_pattern = r'(def collect_data.*?)\n        # Extract data from each target website.*?for site in self\.target_websites\.keys\(\):.*?extract_method\(\).*?\n'
    match = re.search(collect_data_pattern, content, re.DOTALL)
    
    if match:
        # Replace the collect_data loop
        updated_content = content.replace(match.group(0), match.group(1) + "\n" + COLLECT_DATA_UPDATE + "\n")
        
        # Write the updated content back to the file
        with open(coffee_market_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        logger.info("Successfully integrated GraphQL extractor into coffee_market.py")
        return True
    else:
        logger.error("Could not find the collect_data method in coffee_market.py")
        return False

if __name__ == "__main__":
    print("\n🚀 INTEGRATING FOODPANDA GRAPHQL EXTRACTOR INTO COFFEE MARKET DATA COLLECTOR\n")
    
    # Check dependencies
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright dependency found")
    except ImportError:
        print("❌ Playwright not installed. Please install it using: pip install playwright")
        print("   After installation, run: playwright install chromium")
        exit(1)
    
    # Check if required modules exist
    required_files = [
        "foodpanda_graphql_extractor.py",
        "foodpanda_graphql_integration.py"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        exit(1)
    
    print("✅ All required files found")
    
    # Confirm with the user
    print("\nWARNING: This script will modify coffee_market.py.")
    print("A backup will be created before making any changes.")
    confirmation = input("Continue? (y/n): ")
    
    if confirmation.lower() != 'y':
        print("Integration canceled.")
        exit(0)
    
    # Integrate the extractor
    if integrate_graphql_extractor():
        print("\n✅ Integration successful!")
        print("You can now use the extract_foodpanda_graphql_data method in your coffee market data collector.")
        print("The collect_data method has been updated to use GraphQL extraction for Foodpanda.")
    else:
        print("\n❌ Integration failed. Please check the logs for details.")
