"""
Enhanced extraction module for Naheed.pk coffee products
"""

import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def extract_naheed_products(soup, website_config):
    """
    Extract coffee product data from Naheed using enhanced selectors.
    
    Args:
        soup (BeautifulSoup): HTML content from Naheed's website
        website_config (dict): Configuration dictionary for Naheed website
    
    Returns:
        list: Extracted products
    """
    # Save HTML for debugging if needed
    with open("naheed_debug.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
        
    logger.info("Trying to find Naheed products with primary selector")
    
    # Extract product items using the specified CSS selector
    product_selector = website_config['product_selector']
    product_cards = soup.select(product_selector)
    
    if not product_cards:
        logger.warning(f"No product cards found on Naheed using selector: {product_selector}")
        # Try alternative selectors from the configuration
        alternative_selectors = website_config['alternative_selectors']['product_selector']
        for selector in alternative_selectors:
            logger.info(f"Trying alternative product selector: {selector}")
            product_cards = soup.select(selector)
            if product_cards:
                logger.info(f"Found {len(product_cards)} products using alternative selector: {selector}")
                break
    else:
        logger.info(f"Found {len(product_cards)} products using primary selector")
        
    if not product_cards:
        logger.warning("Failed to find any products with all selectors")
        return []
        
    logger.info(f"Processing {len(product_cards)} product cards from Naheed")
    
    products = []
    
    for card in product_cards:
        try:
            product_data = {}
            
            # Extract name using the specific selector from configuration
            name_selector = website_config['name_selector']
            name_elem = card.select_one(name_selector)
            
            if not name_elem:
                logger.debug(f"Name not found with primary selector: {name_selector}")
                # Try alternative selectors if main selector fails
                alternative_name_selectors = [
                    '.product-item-name .product-item-link',
                    '.product-name a',
                    '.product-item-link'
                ]
                for selector in alternative_name_selectors:
                    name_elem = card.select_one(selector)
                    if name_elem:
                        logger.debug(f"Found name using alternative selector: {selector}")
                        break
                        
                # If still not found, try configured alternatives
                if not name_elem:
                    for selector in website_config['alternative_selectors']['name_selector']:
                        name_elem = card.select_one(selector)
                        if name_elem:
                            logger.debug(f"Found name using configured alternative selector: {selector}")
                            break
            
            if name_elem:
                product_data['name'] = name_elem.text.strip()
                logger.debug(f"Extracted product name: {product_data['name']}")
            else:
                logger.warning("Could not find product name with any selector")
                product_data['name'] = "Unknown"
            
            # Extract price
            price_elem = card.select_one(website_config['price_selector'])
            if not price_elem:
                price_elem = card.select_one('.price')
            if not price_elem:
                for selector in website_config['alternative_selectors']['price_selector']:
                    price_elem = card.select_one(selector)
                    if price_elem:
                        break
                        
            price_text = price_elem.text.strip() if price_elem else "0"
            # Clean price text (remove "Rs. " and commas)
            price_text = price_text.replace("Rs.", "").replace("PKR", "").replace(",", "").strip()
            try:
                product_data['price'] = float(price_text)
                logger.debug(f"Extracted price: {product_data['price']}")
            except ValueError:
                logger.warning(f"Could not convert price text: {price_text}")
                product_data['price'] = 0
            
            # Source website
            product_data['source'] = 'naheed.pk'
            
            # Naheed doesn't show ratings directly in search results
            product_data['rating'] = 0
            product_data['reviews_count'] = 0
            
            # Skip non-coffee products
            if any(coffee_term in product_data['name'].lower() for coffee_term in 
                  ['coffee', 'caffè', 'espresso', 'cappuccino', 'mocha', 'latte']):
                products.append(product_data)
            else:
                logger.debug(f"Skipping non-coffee product: {product_data['name']}")
                
        except Exception as e:
            logger.error(f"Error processing Naheed product card: {e}")
    
    logger.info(f"Extracted {len(products)} coffee products from Naheed")
    return products

# Function to integrate into the main collector
def integrate_naheed_extraction(collector, soup):
    """
    Integration function to use with the main collector
    
    Args:
        collector: The main CoffeeMarketDataCollector instance
        soup: BeautifulSoup object for the Naheed page
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        products = extract_naheed_products(soup, collector.target_websites['naheed'])
        
        for product_data in products:
            # Extract additional details
            product_data['brand'] = collector._extract_brand(product_data['name'])
            product_data['type'] = collector._extract_coffee_type(product_data['name'])
            product_data['packaging'] = collector._extract_packaging_info(product_data['name'])
            product_data['price_tier'] = collector._get_price_tier(product_data['price'])
            
            # Add to raw data collection
            collector.raw_data.append(product_data)
            
            # Add to processed categories
            collector.processed_data['products'].append(product_data)
            collector._update_aggregated_data(product_data)
            
        return len(products) > 0
        
    except Exception as e:
        logger.error(f"Error in Naheed integration: {e}")
        return False
