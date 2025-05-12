"""
Fixed version of the coffee market data collector script.
This version includes:
1. Fixed price extraction for Daraz
2. Full pagination support for Daraz to get all 102 pages
3. Infinite scrolling implementation for Alfatah
"""

import os
import sys
import shutil
import logging
import re
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"coffee_fixes_applied_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def apply_fixes():
    """
    Apply all fixes to the coffee market data collector script.
    """
    coffee_market_path = os.path.join('src', 'data_collection', 'coffee_market.py')
    
    if not os.path.exists(coffee_market_path):
        logger.error(f"Could not find {coffee_market_path}")
        return False
    
    # Create a backup of the original file
    backup_path = coffee_market_path + '.backup'
    shutil.copy2(coffee_market_path, backup_path)
    logger.info(f"Created backup of original file at {backup_path}")
    
    # Read the original file content
    with open(coffee_market_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import for BeautifulSoup if needed
    if 'from bs4 import BeautifulSoup' not in content:
        content = content.replace(
            'import re',
            'import re\nfrom bs4 import BeautifulSoup'
        )
    
    # Replace the Daraz method implementation
    content = replace_daraz_method(content)
    
    # Add the Alfatah infinite scroll method
    content = add_alfatah_infinite_scroll_method(content)
    
    # Update the collect_data method to use the new Alfatah method
    content = update_collect_data_method(content)
    
    # Write the modified content back to the file
    with open(coffee_market_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Successfully applied all fixes to {coffee_market_path}")
    return True

def replace_daraz_method(content):
    """Replace the Daraz extraction method with the fixed version"""
    
    # Define the new Daraz method implementation
    new_daraz_method = """    def extract_daraz_data(self, max_pages=102):
        \"\"\"
        Extract coffee product data from Daraz with improved price extraction and full pagination support.
        
        Args:
            max_pages (int): Maximum number of pages to scrape (default is 102 for Daraz)
        \"\"\"
        logger.info("Extracting coffee data from Daraz with improved price extraction and pagination")
        
        base_url = self.target_websites['daraz']['search_url']
        if not isinstance(base_url, str):
            logger.warning(f"Daraz URL is not a string: {type(base_url)}")
            return
        
        total_products = 0
        
        for page in range(1, max_pages + 1):
            # Generate URL for current page
            current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'daraz')
            logger.info(f"Processing Daraz page {page}/{max_pages} with URL: {current_url}")
            
            # Use selenium to handle JavaScript rendered content
            soup = self.get_page_content(current_url, use_selenium=True)
            if not soup:
                logger.warning(f"Failed to get Daraz content for page {page}")
                break

            # Save HTML for debugging (only first page)
            if page == 1:
                with open("daraz_debug.html", "w", encoding="utf-8") as f:
                    f.write(str(soup))
            
            # Extract product cards using selectors
            product_selector = self.target_websites['daraz']['product_selector']
            product_cards = soup.select(product_selector)
            
            # Try alternative selectors if primary selector fails
            if not product_cards:
                alternative_selectors = self.target_websites['daraz']['alternative_selectors']['product_selector']
                for selector in alternative_selectors:
                    logger.info(f"Trying alternative product selector for Daraz: {selector}")
                    product_cards = soup.select(selector)
                    if product_cards:
                        logger.info(f"Found {len(product_cards)} products using alternative selector: {selector}")
                        break
            
            if not product_cards:
                logger.warning(f"Failed to find any products with all selectors for Daraz on page {page}")
                continue
            
            logger.info(f"Processing {len(product_cards)} product cards from Daraz page {page}")
            page_product_count = 0

            for card in product_cards:
                try:
                    product_data = {}
                    
                    # Extract product name
                    name_selector = self.target_websites['daraz']['name_selector']
                    name_elem = card.select_one(name_selector)

                    if not name_elem:
                        for selector in self.target_websites['daraz']['alternative_selectors']['name_selector']:
                            name_elem = card.select_one(selector)
                            if name_elem:
                                break
                    
                    product_data['name'] = name_elem.text.strip() if name_elem else "Unknown"

                    # FIXED: Improved price extraction logic for Daraz
                    price_elem = None
                    
                    # Try all possible price selectors
                    price_selectors = [
                        '.price--NVB62',
                        '.currency--GVKjl',
                        'span[data-price]',
                        'div.price', 
                        '.pdp-price',
                        '.product-price',
                        '[data-qa-locator="product-price"]'
                    ]
                    
                    for selector in price_selectors:
                        price_elem = card.select_one(selector)
                        if price_elem:
                            break
                    
                    if price_elem and price_elem.has_attr('data-price'):
                        # Get price from data attribute if available
                        try:
                            product_data['price'] = float(price_elem['data-price'])
                        except (ValueError, TypeError):
                            product_data['price'] = 0
                    else:
                        # Extract from text content
                        price_text = price_elem.text.strip() if price_elem else "0"
                        
                        # Clean price text thoroughly
                        price_text = re.sub(r'[^0-9.]', '', price_text.replace(',', '').replace('Rs.', '').replace('PKR', ''))
                        
                        try:
                            product_data['price'] = float(price_text) if price_text else 0
                        except ValueError:
                            product_data['price'] = 0

                    # Extract rating
                    rating_elem = card.select_one('.rating--b2Qtx')
                    if rating_elem:
                        try:
                            product_data['rating'] = float(rating_elem.text.strip())
                        except ValueError:
                            product_data['rating'] = 0
                    else:
                        product_data['rating'] = 0

                    # Extract review count
                    reviews_elem = card.select_one('.rating__review--ygkUy')
                    reviews_text = reviews_elem.text.strip() if reviews_elem else "0"
                    reviews_count = ''.join(filter(str.isdigit, reviews_text))
                    product_data['reviews_count'] = int(reviews_count) if reviews_count else 0

                    # Add metadata
                    product_data['source'] = 'daraz.pk'
                    product_data['brand'] = self._extract_brand(product_data['name'])
                    product_data['type'] = self._extract_coffee_type(product_data['name'])
                    product_data['packaging'] = self._extract_packaging_info(product_data['name'])
                    product_data['price_tier'] = self._get_price_tier(product_data['price'])

                    # Store the data
                    self.raw_data.append(product_data)
                    self.processed_data['products'].append(product_data)
                    self._update_aggregated_data(product_data)

                    page_product_count += 1
                    total_products += 1
                    
                    # Add a log to confirm price extraction worked
                    logger.debug(f"Extracted product: {product_data['name']} with price: {product_data['price']}")
                    
                except Exception as e:
                    logger.error(f"Error processing Daraz product card on page {page}: {e}")
                    # Print traceback for debugging
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

            logger.info(f"Extracted {page_product_count} products from Daraz page {page}")
            
            # Break if no products found
            if page_product_count == 0:
                logger.info(f"No products found on page {page}, stopping pagination")
                break
                
            # Add delay between pages to avoid getting blocked
            import time
            import random
            time.sleep(random.uniform(2, 4))

        logger.info(f"Total extracted {total_products} products from Daraz across {min(page, max_pages)} pages")
"""
    
    # Simple approach: find the current extract_daraz_data method and replace it
    # Look for the method signature
    method_signature = "def extract_daraz_data("
    if method_signature in content:
        # Find the method
        method_start = content.find(method_signature)
        
        # Find the start of the next method
        next_method_start = content.find("def ", method_start + len(method_signature))
        
        if next_method_start > 0:
            # Replace the method
            new_content = content[:method_start] + new_daraz_method + content[next_method_start:]
            return new_content
        else:
            logger.warning("Could not find the end of the extract_daraz_data method")
    else:
        logger.warning("Could not find the extract_daraz_data method")
        
    # If we get here, we couldn't properly replace the method
    return content

def add_alfatah_infinite_scroll_method(content):
    """Add the new Alfatah infinite scroll method"""
    
    # Define the new Alfatah infinite scroll method
    new_alfatah_method = """    def extract_alfatah_data_with_infinite_scroll(self, max_pages=10):
        \"\"\"
        Extract coffee product data from Alfatah using infinite scrolling instead of pagination.
        
        Args:
            max_pages (int): Maximum number of scroll iterations to perform
        \"\"\"
        logger.info("Extracting coffee data from Alfatah with infinite scrolling")
        
        base_url = self.target_websites['alfatah']['search_url']
        if not isinstance(base_url, str):
            logger.warning(f"Alfatah URL is not a string: {type(base_url)}")
            return
            
        total_products = 0
        processed_product_ids = set()  # Track products we've already processed
        
        # Initialize Selenium for infinite scrolling
        from selenium import webdriver
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        
        driver = None
        try:
            driver = self.setup_selenium_driver()
            driver.get(base_url)
            
            # Wait for initial page load
            import time
            time.sleep(3)
            
            # Save HTML for debugging (initial page)
            with open("alfatah_debug_initial.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
                
            # Process multiple scroll iterations (each one is like a "page")
            for scroll_num in range(1, max_pages + 1):
                logger.info(f"Performing scroll iteration {scroll_num}/{max_pages} for Alfatah")
                
                # Get current height of page for checking if more content loaded
                last_height = driver.execute_script("return document.body.scrollHeight")
                
                # Scroll to the bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(3)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                # If heights are the same, we've reached the end
                if new_height == last_height:
                    logger.info("Reached the end of the page, no more products to load")
                    break
                    
                # Parse content with BeautifulSoup after scrolling
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Extract product items using the specified CSS selector
                product_selector = self.target_websites['alfatah']['product_selector']
                product_cards = soup.select(product_selector)
                
                if not product_cards:
                    logger.warning(f"No product cards found on Alfatah scroll {scroll_num} using selector: {product_selector}")
                    # Try alternative selectors from the configuration
                    alternative_selectors = self.target_websites['alfatah']['alternative_selectors']['product_selector']
                    for selector in alternative_selectors:
                        logger.info(f"Trying alternative product selector: {selector}")
                        product_cards = soup.select(selector)
                        if product_cards:
                            logger.info(f"Found {len(product_cards)} products using alternative selector: {selector}")
                            break
                else:
                    logger.info(f"Found {len(product_cards)} products using primary selector on scroll {scroll_num}")
                    
                if not product_cards:
                    logger.warning(f"Failed to find any products with all selectors on scroll {scroll_num}")
                    continue
                    
                logger.info(f"Processing {len(product_cards)} product cards from Alfatah scroll {scroll_num}")
                scroll_product_count = 0
                new_product_count = 0
                
                for card in product_cards:
                    try:
                        # Generate a unique product ID using data attributes or inner HTML hash
                        # This helps us track which products we've already processed across scrolls
                        import hashlib
                        product_id = hash(card.get('data-product-id', '') or card.get('id', '') or card.text[:50])
                        
                        # Skip if we've already processed this product
                        if product_id in processed_product_ids:
                            continue
                            
                        processed_product_ids.add(product_id)
                        
                        product_data = {}
                        
                        # Extract name using the specific selector from configuration
                        name_selector = self.target_websites['alfatah']['name_selector']
                        name_elem = card.select_one(name_selector)
                        
                        if not name_elem:
                            # Try alternative selectors if main selector fails
                            for selector in self.target_websites['alfatah']['alternative_selectors']['name_selector']:
                                name_elem = card.select_one(selector)
                                if name_elem:
                                    logger.debug(f"Found name using alternative selector: {selector}")
                                    break
                        
                        if name_elem:
                            product_data['name'] = name_elem.text.strip()
                            logger.debug(f"Extracted product name: {product_data['name']}")
                        else:
                            logger.warning("Could not find product name with any selector")
                            product_data['name'] = "Unknown"
                        
                        # Extract price
                        price_selector = self.target_websites['alfatah']['price_selector']
                        price_elem = card.select_one(price_selector)
                        if not price_elem:
                            for selector in self.target_websites['alfatah']['alternative_selectors']['price_selector']:
                                price_elem = card.select_one(selector)
                                if price_elem:
                                    break
                                    
                        price_text = price_elem.text.strip() if price_elem else "0"
                        # Clean price text (remove "Rs. " and commas)
                        import re
                        price_text = re.sub(r'[^0-9.]', '', price_text.replace(',', ''))
                        try:
                            product_data['price'] = float(price_text)
                        except ValueError:
                            product_data['price'] = 0
                        
                        # Source website
                        product_data['source'] = 'alfatah.pk'
                        
                        # Alfatah doesn't show ratings directly in search results
                        product_data['rating'] = 0
                        product_data['reviews_count'] = 0
                        
                        # Check if this is a coffee product by checking the name
                        if not any(term in product_data['name'].lower() for term in [
                                'coffee', 'caffè', 'espresso', 'cappuccino', 'mocha', 'latte'
                            ]) and product_data['name'] != "Unknown":
                            logger.debug(f"Skipping non-coffee product: {product_data['name']}")
                            continue
                        
                        # Extract additional details from the product name
                        product_data['brand'] = self._extract_brand(product_data['name'])
                        product_data['type'] = self._extract_coffee_type(product_data['name'])
                        product_data['packaging'] = self._extract_packaging_info(product_data['name'])
                        product_data['price_tier'] = self._get_price_tier(product_data['price'])
                        
                        # Add to raw data collection
                        self.raw_data.append(product_data)
                        
                        # Add to processed categories
                        self.processed_data['products'].append(product_data)
                        self._update_aggregated_data(product_data)
                        
                        scroll_product_count += 1
                        new_product_count += 1
                        total_products += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing Alfatah product card: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                
                logger.info(f"Found {scroll_product_count} products, {new_product_count} new products in scroll {scroll_num}")
                
                # If we didn't find any new products, we might have reached the end
                if new_product_count == 0:
                    logger.info(f"No new products found on scroll {scroll_num}, stopping infinite scroll")
                    break
                    
        except Exception as e:
            logger.error(f"Error during Alfatah infinite scrolling: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        finally:
            if driver:
                driver.quit()
        
        logger.info(f"Total extracted {total_products} unique products from Alfatah using infinite scroll")
"""
    
    # Simple approach: add the method before _generate_pagination_url
    method_marker = "def _generate_pagination_url("
    if method_marker in content:
        method_pos = content.find(method_marker)
        # Find the correct indentation level (assuming it's a class method)
        indentation_start = content.rfind("\n", 0, method_pos) + 1
        indentation_end = content.find("def", indentation_start)
        indentation = content[indentation_start:indentation_end]
        
        # Add the new method before the marker
        new_content = content[:method_pos] + new_alfatah_method + "\n\n    " + content[method_pos:]
        return new_content
    else:
        # Alternative: add at the end of extract_alfatah_data method
        alfatah_method = "def extract_alfatah_data("
        if alfatah_method in content:
            method_start = content.find(alfatah_method)
            next_method_pos = content.find("def ", method_start + 10) # Skip current method name
            if next_method_pos > 0:
                new_content = content[:next_method_pos] + new_alfatah_method + "\n\n    " + content[next_method_pos:]
                return new_content
        
        # If no good position found
        logger.warning("Could not find a good position to insert the Alfatah infinite scroll method")
        return content

def update_collect_data_method(content):
    """Update collect_data method to use the new Alfatah infinite scroll method"""
    
    # Find the lines that call alfatah extraction in collect_data
    alfatah_call_pattern = r"elif site_name == 'alfatah':[^}]*?extraction_methods\[site_name\]\(max_pages=\d+\)"
    
    # Replace with call to the new method
    new_alfatah_call = "elif site_name == 'alfatah':\n                        self.extract_alfatah_data_with_infinite_scroll(max_pages=5)"
    
    import re
    new_content = re.sub(alfatah_call_pattern, new_alfatah_call, content)
    
    # Check if the replacement worked
    if new_content == content:
        logger.warning("Failed to update collect_data method - trying alternative approach")
        
        # Try simpler replacement
        simple_pattern = r"extraction_methods\[site_name\]\(max_pages=\d+\)"
        # Check if we have this pattern in the context of alfatah
        alfatah_context = "elif site_name == 'alfatah':"
        alfatah_pos = content.find(alfatah_context)
        if alfatah_pos > 0:
            context_section = content[alfatah_pos:alfatah_pos+500]  # Get some text after alfatah
            if simple_pattern in context_section:
                # Replace just in this section
                modified_section = re.sub(
                    simple_pattern,
                    "self.extract_alfatah_data_with_infinite_scroll(max_pages=5)",
                    context_section
                )
                new_content = content[:alfatah_pos] + modified_section + content[alfatah_pos+len(context_section):]
                logger.info("Successfully updated collect_data method using alternative approach")
    else:
        logger.info("Successfully updated collect_data method")
    
    return new_content

if __name__ == "__main__":
    print("Applying fixes to coffee market data collector...")
    success = apply_fixes()
    
    if success:
        print("✅ Successfully applied all fixes!")
        print("   1. Fixed Daraz price extraction")
        print("   2. Implemented full pagination for Daraz (102 pages)")
        print("   3. Added infinite scrolling support for Alfatah")
        print("   4. Updated the collect_data method to use the new methods")
        print("\nYou can now run the improved coffee market data collector.")
    else:
        print("❌ Failed to apply fixes. Check the log file for details.")
