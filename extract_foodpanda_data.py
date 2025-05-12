import os
import re
import json
from bs4 import BeautifulSoup
import datetime
import argparse

def extract_coffee_products_from_html(html_path, debug=False):
    """
    Extract coffee product data from a Foodpanda HTML file.
    
    Args:
        html_path (str): Path to the HTML file containing Foodpanda coffee product listings
        debug (bool): Enable debug mode with extra logging
        
    Returns:
        list: List of dictionaries containing extracted coffee product information
    """
    # Check if the file exists
    if not os.path.isfile(html_path):
        print(f"Error: File '{html_path}' does not exist.")
        return []
    
    # Read the HTML file
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
            if debug:
                print(f"Successfully read {len(html_content)} bytes from {html_path}")
    except UnicodeDecodeError:
        print("Error with UTF-8 encoding, trying with alternative encoding...")
        try:
            with open(html_path, 'r', encoding='latin-1') as file:
                html_content = file.read()
                if debug:
                    print(f"Successfully read {len(html_content)} bytes with latin-1 encoding")
        except Exception as e:
            print(f"Error reading file with alternative encoding: {e}")
            return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    # Parse the HTML content
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        if debug:
            print(f"Successfully parsed HTML content")
    except Exception as e:
        print(f"Error parsing HTML content: {e}")
        return []
    
    # Extract products from the parsed HTML
    products = []
    
    # Find all product cards - Try multiple possible selectors
    product_cards = []
    selectors = [
        '.groceries-product-card',  # Primary selector for Pandamart
        '.dish-card',               # Alternative selector for some Foodpanda pages
        'ul.product-grid > li'      # Generic fallback selector
    ]
    
    for selector in selectors:
        product_cards = soup.select(selector)
        if product_cards:
            if debug:
                print(f"Found {len(product_cards)} product cards using selector: {selector}")
            break
    
    print(f"Found {len(product_cards)} product cards.")
    
    # Process each product card
    for card in product_cards:
        try:
            # Create a dictionary to store product data
            product_data = {
                'id': card.get('data-id', '').replace('product-', '') if card.has_attr('data-id') else '',
                'scraped_at': datetime.datetime.now().isoformat()
            }
            
            # Extract product name
            name_elem = card.select_one('.groceries-product-card-name')
            if name_elem:
                product_data['name'] = name_elem.text.strip()
            else:
                product_data['name'] = "Unknown"
            
            # Skip if the product name doesn't contain 'coffee' or related terms
            if not is_coffee_product(product_data['name']):
                continue
            
            # Extract product price
            price_elem = card.select_one('.groceries-product-card-price')
            price_text = price_elem.text.strip() if price_elem else "0"
            
            # Clean price text (remove "Rs. " and commas)
            price_text = price_text.replace("Rs.", "").replace("PKR", "").replace("₨", "").replace(",", "").strip()
            try:
                product_data['price'] = float(price_text)
            except ValueError:
                # Try to extract numbers from the text if parsing fails
                numbers = re.findall(r'\d+\.?\d*', price_text)
                product_data['price'] = float(numbers[0]) if numbers else 0
            
            # Extract product image URL
            img_elem = card.select_one('.groceries-image')
            if img_elem and img_elem.has_attr('src'):
                product_data['image_url'] = img_elem['src']
            elif img_elem and img_elem.has_attr('data-src'):
                product_data['image_url'] = img_elem['data-src']
            else:
                product_data['image_url'] = ""
            
            # Extract product URL
            nav_wrapper = card.find_parent('a')
            if nav_wrapper and nav_wrapper.has_attr('href'):
                product_data['product_url'] = f"https://www.foodpanda.pk{nav_wrapper['href']}"
            else:
                product_data['product_url'] = ""
            
            # Set source website
            product_data['source'] = 'foodpanda.pk'
              # Extract brand from product name
            product_data['brand'] = extract_brand(product_data['name'])
            
            # Extract metadata if visible in the HTML
            # Add vendor code if available
            product_card_elem = card.find_parent('.groceries-product-card')
            if product_card_elem and product_card_elem.has_attr('data-vendor-sponsoring'):
                vendor_info = product_card_elem.get('data-vendor-sponsoring', '')
                product_data['vendor_info'] = vendor_info
            
            # Add product ID from the parent element if available and not already set
            if not product_data['id']:
                parent_with_id = card.find_parent(attrs={'data-id': True})
                if parent_with_id:
                    product_data['id'] = parent_with_id.get('data-id', '').replace('product-', '')
            
            # Add to products list
            products.append(product_data)
            
        except Exception as e:
            print(f"Error processing product card: {e}")
    
    print(f"Successfully extracted {len(products)} coffee products.")
    return products

def is_coffee_product(name):
    """
    Check if a product name indicates a coffee product.
    
    Args:
        name (str): Product name to check
        
    Returns:
        bool: True if the product is likely a coffee product, False otherwise
    """
    name_lower = name.lower()
    coffee_keywords = ['coffee', 'café', 'cafe', 'espresso', 'cappuccino', 'latte', 'mocha', 
                      'americano', 'nescafe', 'folgers', 'lavazza', 'illy', 'maxwell', 
                      'starbucks', 'arabica', 'robusta']
    
    # Check if any of the coffee keywords are in the product name
    for keyword in coffee_keywords:
        if keyword in name_lower:
            # Exclude non-coffee products that might contain coffee keywords
            # but aren't actually coffee (like coffee tables, coffee mugs, etc.)
            exclusion_keywords = ['mug', 'cup', 'table', 'creamer', 'machine', 'maker', 'filter']
            for exclusion in exclusion_keywords:
                if exclusion in name_lower and 'coffee ' + exclusion in name_lower:
                    return False
            return True
    
    return False

def extract_brand(name):
    """
    Extract brand name from product name.
    
    Args:
        name (str): Product name
        
    Returns:
        str: Extracted brand name or "Unknown" if no brand could be determined
    """
    # List of common coffee brands
    known_brands = {
        'nescafe': 'Nescafe',
        'nestle': 'Nestle',
        'lavazza': 'Lavazza',
        'folgers': 'Folgers',
        'maxwell': 'Maxwell House',
        'starbucks': 'Starbucks', 
        'illy': 'Illy',
        'nespresso': 'Nespresso',
        'davidoff': 'Davidoff',
        'jacobs': 'Jacobs',
        'douwe egberts': 'Douwe Egberts',
        'kenco': 'Kenco',
        'tasters': 'Tasters Choice',
        'moccona': 'Moccona',
        'carte noire': 'Carte Noire',
        'gold roast': 'Gold Roast',
        'klassno': 'Klassno'
    }
    
    name_lower = name.lower()
    
    # Check if any known brand appears in the product name
    for brand_keyword, brand_name in known_brands.items():
        if brand_keyword in name_lower:
            return brand_name
    
    # If no known brand is found, check for potential brand at the beginning of the name
    words = name.split()
    if len(words) >= 2:
        # First word might be a brand
        potential_brand = words[0].strip()
        if len(potential_brand) > 2 and potential_brand.lower() not in ['the', 'new', 'old', 'buy']:
            return potential_brand
    
    return "Unknown"

def save_to_json(data, output_file):
    """
    Save extracted data to a JSON file.
    
    Args:
        data (list): List of product dictionaries
        output_file (str): Path to the output JSON file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data successfully saved to {output_file}")
    except Exception as e:
        print(f"Error saving data to file: {e}")

# Add function to help categorize coffee products
def categorize_coffee_products(products):
    """
    Add additional categorization to coffee products.
    
    Args:
        products (list): List of product dictionaries
        
    Returns:
        list: Enhanced product dictionaries with categorization
    """
    for product in products:
        # Categorize by type
        name_lower = product['name'].lower()
        
        # Determine coffee type
        if any(term in name_lower for term in ['instant', 'classic', 'gold']):
            product['type'] = 'instant'
        elif any(term in name_lower for term in ['ground', 'filter']):
            product['type'] = 'ground'
        elif any(term in name_lower for term in ['bean', 'whole']):
            product['type'] = 'beans'
        elif any(term in name_lower for term in ['capsule', 'pod']):
            product['type'] = 'capsules'
        elif any(term in name_lower for term in ['3 in 1', '3in1', '2 in 1', '2in1']):
            product['type'] = 'mix'
        elif any(term in name_lower for term in ['sachet', 'packet']):
            product['type'] = 'instant'
        else:
            product['type'] = 'other'
            
        # Try to extract packaging information
        product['packaging'] = extract_packaging_info(product['name'])
        
        # Determine price tier
        if product['price'] == 0:
            product['price_tier'] = 'unknown'
        elif product['price'] < 500:
            product['price_tier'] = 'low'
        elif product['price'] < 1500:
            product['price_tier'] = 'medium'
        else:
            product['price_tier'] = 'high'
    
    return products

def extract_packaging_info(name):
    """
    Extract packaging information from product name.
    
    Args:
        name (str): Product name
        
    Returns:
        dict: Packaging information with value, unit, and display
    """
    packaging_info = {
        'value': 0,
        'unit': 'unknown',
        'display': 'unknown'
    }
    
    # Look for common packaging patterns like "50g", "100ml", "200 g", "1 kg", etc.
    patterns = [
        r'(\d+(?:\.\d+)?)\s*([gG][mM]?)',  # For grams (50g, 50gm, etc.)
        r'(\d+(?:\.\d+)?)\s*([mM][lL])',   # For milliliters (200ml, 200ML, etc.)
        r'(\d+(?:\.\d+)?)\s*([kK][gG])',   # For kilograms (1kg, 2KG, etc.)
        r'(\d+(?:\.\d+)?)\s*([lL])',       # For liters (1l, 2L, etc.)
        r'(\d+(?:\.\d+)?)\s*([oO][zZ])',   # For ounces (8oz, 16OZ, etc.)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2).lower()
                
                # Standardize units
                if unit in ['g', 'gm', 'gr', 'gram', 'grams']:
                    unit = 'g'
                elif unit in ['ml', 'milliliter', 'milliliters']:
                    unit = 'ml'
                elif unit in ['l', 'ltr', 'liter', 'liters']:
                    unit = 'l'
                elif unit in ['kg', 'kilo', 'kilos', 'kilogram', 'kilograms']:
                    unit = 'kg'
                elif unit in ['oz', 'ounce', 'ounces']:
                    unit = 'oz'
                
                packaging_info['value'] = value
                packaging_info['unit'] = unit
                packaging_info['display'] = f"{value}{unit}"
                return packaging_info
            except ValueError:
                pass
    
    return packaging_info

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract coffee product data from Foodpanda HTML file')
    parser.add_argument('-i', '--input', default="foodpanda_debug.html", help='Path to HTML file')
    parser.add_argument('-o', '--output', default="extracted_coffee_products.json", help='Path to output JSON file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode with extra logging')
    parser.add_argument('-s', '--summary', action='store_true', help='Show summary statistics after extraction')
    args = parser.parse_args()
    
    # Use absolute paths if not provided
    if not os.path.isabs(args.input):
        args.input = os.path.join(os.getcwd(), args.input)
    if not os.path.isabs(args.output):
        args.output = os.path.join(os.getcwd(), args.output)
    
    print(f"Extracting coffee products from: {args.input}")
    print(f"Saving results to: {args.output}")
    
    # Extract products with debug flag if specified
    products = extract_coffee_products_from_html(args.input, debug=args.debug)
    if products:
        # Enhance product data with categorization
        enhanced_products = categorize_coffee_products(products)
        save_to_json(enhanced_products, args.output)
        
        # Show summary statistics if requested
        if args.summary:
            print("\nSummary Statistics:")
            print(f"Total products: {len(enhanced_products)}")
            
            # Brands breakdown
            brands = {}
            for product in enhanced_products:
                brand = product['brand']
                brands[brand] = brands.get(brand, 0) + 1
            print("\nBrands breakdown:")
            for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
                print(f"  {brand}: {count} products")
            
            # Coffee types breakdown
            types = {}
            for product in enhanced_products:
                coffee_type = product['type']
                types[coffee_type] = types.get(coffee_type, 0) + 1
            print("\nCoffee types breakdown:")
            for coffee_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {coffee_type}: {count} products")
            
            # Price tiers breakdown
            price_tiers = {}
            for product in enhanced_products:
                tier = product['price_tier']
                price_tiers[tier] = price_tiers.get(tier, 0) + 1
            print("\nPrice tiers breakdown:")
            for tier, count in sorted(price_tiers.items(), key=lambda x: x[1], reverse=True):
                print(f"  {tier}: {count} products")
            
            # Price statistics
            prices = [product['price'] for product in enhanced_products]
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                print(f"\nPrice statistics:")
                print(f"  Average price: Rs. {avg_price:.2f}")
                print(f"  Minimum price: Rs. {min_price:.2f}")
                print(f"  Maximum price: Rs. {max_price:.2f}")
