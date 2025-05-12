#!/usr/bin/env python
"""
A simpler test script that only uses the extracted foodpanda HTML to test our implementation
"""

import os
import sys
import logging
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class SimpleFoodpandaExtractor:
    """A simplified version of the extraction logic"""
    
    def __init__(self):
        self.products = []
        
    def is_coffee_product(self, product_name):
        """Check if a product is coffee-related based on its name"""
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
    
    def extract_brand(self, product_name):
        """Extract brand name from product name"""
        # Common coffee brands in Pakistan
        common_brands = [
            'Nescafe', 'Nestle', 'Lavazza', 'Davidoff', 'Jacobs', 'Maxwell House', 
            'Folgers', 'Mehran', 'National', 'Tapal', 'Espresso', 'Koffee Kult', 
            'MacCoffee', 'Kenco', 'Illy', 'Continental'
        ]
            
        for brand in common_brands:
            if brand.lower() in product_name.lower():
                return brand
        
        # If no known brand is found
        return "Unknown"
    
    def extract_coffee_type(self, product_name):
        """Extract coffee type from product name"""
        name_lower = product_name.lower()
        
        if 'instant' in name_lower:
            return 'instant'
        elif 'ground' in name_lower or 'grind' in name_lower:
            return 'ground'
        elif 'bean' in name_lower or 'whole' in name_lower:
            return 'beans'
        elif 'powder' in name_lower or 'powdered' in name_lower:
            return 'powdered'
        else:
            # Try to infer from other keywords
            if 'capsule' in name_lower or 'pod' in name_lower:
                return 'capsule/pod'
            elif 'mix' in name_lower or '3 in 1' in name_lower:
                return 'coffee mix'
            
            # Default to instant as it's most common
            return 'instant'
    
    def extract_from_html(self, html_file):
        """Extract products from saved HTML file"""
        logger.info(f"Extracting products from {html_file}")
        
        # Check if the file exists
        if not os.path.exists(html_file):
            logger.error(f"File not found: {html_file}")
            return
        
        # Load the HTML content
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try various CSS selectors to find product cards
        selectors = [
            '.dish-card',
            '.product-card',
            '.product-item',
            '.product',
            'ul.product-grid > li',
            '.groceries-products-list .dish-card'
        ]
        
        product_cards = []
        for selector in selectors:
            product_cards = soup.select(selector)
            if product_cards:
                logger.info(f"Found {len(product_cards)} product cards using selector: {selector}")
                break
        
        if not product_cards:
            logger.warning("No product cards found with any selector")
            return
        
        # Process each product card
        for card in product_cards:
            try:
                product_data = {}
                
                # Extract name
                name_selectors = [
                    '.dish-name',
                    '.product-name',
                    '.title',
                    '.name',
                    '.groceries-product-card-name'
                ]
                
                name_elem = None
                for selector in name_selectors:
                    name_elem = card.select_one(selector)
                    if name_elem:
                        break
                
                if name_elem:
                    product_data['name'] = name_elem.text.strip()
                else:
                    logger.warning("Could not find product name")
                    product_data['name'] = "Unknown"
                
                # Skip non-coffee products
                if not self.is_coffee_product(product_data['name']):
                    logger.debug(f"Skipping non-coffee product: {product_data['name']}")
                    continue
                
                # Extract price
                price_selectors = [
                    '.price',
                    '.discount-price',
                    '.product-price',
                    '.amount',
                    '.groceries-product-card-price'
                ]
                
                price_elem = None
                for selector in price_selectors:
                    price_elem = card.select_one(selector)
                    if price_elem:
                        break
                
                price_text = price_elem.text.strip() if price_elem else "0"
                price_text = price_text.replace("Rs.", "").replace("PKR", "").replace("₨", "").replace(",", "").strip()
                
                try:
                    product_data['price'] = float(price_text)
                except ValueError:
                    # Try to extract numbers from the text if parsing fails
                    numbers = re.findall(r'\d+\.?\d*', price_text)
                    product_data['price'] = float(numbers[0]) if numbers else 0
                
                # Extract image URL
                img_elem = card.select_one('img.groceries-image') or card.select_one('img')
                if img_elem and img_elem.has_attr('src'):
                    product_data['image_url'] = img_elem['src']
                elif img_elem and img_elem.has_attr('data-src'):
                    product_data['image_url'] = img_elem['data-src']
                else:
                    product_data['image_url'] = ""
                
                # Add derived information
                product_data['brand'] = self.extract_brand(product_data['name'])
                product_data['type'] = self.extract_coffee_type(product_data['name'])
                product_data['source'] = 'foodpanda.pk'
                
                self.products.append(product_data)
                
            except Exception as e:
                logger.error(f"Error processing product card: {e}")
        
        logger.info(f"Extracted {len(self.products)} coffee products")
        
        # Save results to file for inspection
        if self.products:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"simple_foodpanda_results_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2)
            logger.info(f"Saved results to {output_file}")
            
            # Show sample output
            logger.info("\nSample Products:")
            for i, product in enumerate(self.products[:min(5, len(self.products))]):
                logger.info(f"\nProduct {i+1}:")
                logger.info(f"  Name: {product.get('name', 'Unknown')}")
                logger.info(f"  Price: {product.get('price', 0)}")
                logger.info(f"  Brand: {product.get('brand', 'Unknown')}")
                logger.info(f"  Type: {product.get('type', 'Unknown')}")
                img_url = product.get('image_url', '')
                logger.info(f"  Image URL: {img_url[:50]}..." if img_url else "  Image URL: None")

if __name__ == "__main__":
    # Check if there's an existing debug HTML file
    html_file = "foodpanda_debug.html"
    
    if not os.path.exists(html_file):
        logger.warning(f"HTML file not found: {html_file}")
        logger.info("Checking for other HTML files...")
        
        # Check for any HTML file with "foodpanda" in the name
        html_files = [f for f in os.listdir('.') if f.endswith('.html') and 'foodpanda' in f.lower()]
        
        if html_files:
            html_file = html_files[0]
            logger.info(f"Found alternative HTML file: {html_file}")
        else:
            logger.error("No foodpanda HTML files found. Run the extraction method to generate one.")
            sys.exit(1)
    
    # Process the HTML file
    extractor = SimpleFoodpandaExtractor()
    extractor.extract_from_html(html_file)
