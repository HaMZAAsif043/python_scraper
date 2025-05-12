"""
Fix for the Foodpanda data extraction method in coffee_market.py
This updated method properly extracts coffee product data from Foodpanda's Pandamart pages.
"""

def extract_foodpanda_data(self, max_pages=3):
    """
    Extract coffee product data from Foodpanda/Pandamart.
    
    Args:
        max_pages (int): Maximum number of pages to scrape
    """
    import re
    import hashlib
    import traceback
    from datetime import datetime
    
    logger.info("Extracting coffee data from Foodpanda")
    
    base_url = self.target_websites['foodpanda']['search_url']
    if not isinstance(base_url, str):
        logger.warning(f"Foodpanda URL is not a string: {type(base_url)}")
        return
        
    total_products = 0
    
    # Initialize product hash set if it doesn't exist
    if not hasattr(self, 'processed_product_hashes'):
        self.processed_product_hashes = set()
    
    # Process multiple pages
    for page in range(1, max_pages + 1):
        # Generate URL for current page
        current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'foodpanda')
        logger.info(f"Processing Foodpanda page {page} with URL: {current_url}")
        
        # Use Selenium to load dynamic content (required for Foodpanda)
        soup = self.get_page_content(current_url, use_selenium=True)
        
        if not soup:
            logger.warning(f"Failed to get Foodpanda content for page {page}")
            break
        
        # For debugging purposes, save the first page's HTML
        if page == 1:
            with open("foodpanda_debug.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
        
        # Check if we're on a 404/error page
        if soup.select_one('.not-found-page') or soup.select_one('.error-page'):
            logger.warning("Detected 404/error page, stopping pagination")
            break
        
        # Try multiple strategies to find product cards
        product_cards = []
        selectors_to_try = [
            'ul.product-grid > li',  # Direct product grid items
            '.groceries-product-card',  # Pandamart-specific cards
            '.dish-card',  # Standard Foodpanda dish cards
            '.product-card',  # Generic product cards
            '.product-item'  # More generic product cards
        ]
        
        # First try the ones we know work for this structure
        for selector in selectors_to_try:
            product_cards = soup.select(selector)
            if product_cards:
                logger.info(f"Found {len(product_cards)} products with selector: {selector}")
                break
        
        # If the above didn't work, try configured selectors
        if not product_cards:
            try:
                product_selector = self.target_websites['foodpanda']['product_selector']
                product_cards = soup.select(product_selector)
                if product_cards:
                    logger.info(f"Found {len(product_cards)} products with configured selector: {product_selector}")
            except (KeyError, AttributeError) as e:
                logger.warning(f"Error with configured product selector: {e}")
        
        # Last try: alternative selectors from configuration
        if not product_cards and 'alternative_selectors' in self.target_websites.get('foodpanda', {}):
            try:
                for alt_selector in self.target_websites['foodpanda']['alternative_selectors'].get('product_selector', []):
                    product_cards = soup.select(alt_selector)
                    if product_cards:
                        logger.info(f"Found {len(product_cards)} products with alternative selector: {alt_selector}")
                        break
            except Exception as e:
                logger.warning(f"Error trying alternative selectors: {e}")
        
        if not product_cards:
            logger.warning(f"No product cards found on Foodpanda page {page}, stopping pagination")
            break
            
        logger.info(f"Processing {len(product_cards)} product cards from Foodpanda page {page}")
        page_product_count = 0
        
        # Process each product card
        for card in product_cards:
            try:
                product_data = {
                    'id': f"foodpanda_{datetime.now().timestamp()}_{total_products}",
                    'scraped_at': datetime.now().isoformat()
                }
                
                # ---- Extract product name ----
                # 1. Try the most specific class for Pandamart first
                name_elem = card.select_one('.groceries-product-card-name')
                
                # 2. Try dish name class (standard Foodpanda format)
                if not name_elem:
                    name_elem = card.select_one('.dish-name')
                
                # 3. Try configured selector if available
                if not name_elem and 'name_selector' in self.target_websites.get('foodpanda', {}):
                    name_elem = card.select_one(self.target_websites['foodpanda']['name_selector'])
                
                # 4. Try alternative selectors from configuration
                if not name_elem and 'alternative_selectors' in self.target_websites.get('foodpanda', {}):
                    for selector in self.target_websites['foodpanda']['alternative_selectors'].get('name_selector', []):
                        name_elem = card.select_one(selector)
                        if name_elem:
                            break
                
                # 5. Try any generic product name classes 
                if not name_elem:
                    for selector in ['.product-name', '.title', 'h2', '.name', '.product-title']:
                        name_elem = card.select_one(selector)
                        if name_elem:
                            break
                
                # If we found a name element, extract the text, otherwise skip this product
                if name_elem:
                    product_data['name'] = name_elem.text.strip()
                    logger.debug(f"Found product name: {product_data['name']}")
                else:
                    logger.warning("Could not find product name, skipping product")
                    continue
                
                # Skip non-coffee products
                if not self._is_coffee_product(product_data['name']):
                    logger.debug(f"Skipping non-coffee product: {product_data['name']}")
                    continue
                
                # ---- Extract product price ----
                # 1. Try the most specific class for Pandamart first
                price_elem = card.select_one('.groceries-product-card-price')
                
                # 2. Try standard Foodpanda price class
                if not price_elem:
                    price_elem = card.select_one('.price')
                
                # 3. Try configured selector if available
                if not price_elem and 'price_selector' in self.target_websites.get('foodpanda', {}):
                    price_elem = card.select_one(self.target_websites['foodpanda']['price_selector'])
                
                # 4. Try alternative selectors from configuration
                if not price_elem and 'alternative_selectors' in self.target_websites.get('foodpanda', {}):
                    for selector in self.target_websites['foodpanda']['alternative_selectors'].get('price_selector', []):
                        price_elem = card.select_one(selector)
                        if price_elem:
                            break
                
                # 5. Try any generic price classes
                if not price_elem:
                    for selector in ['.amount', '.cost', 'span.price', '.product-price']:
                        price_elem = card.select_one(selector)
                        if price_elem:
                            break
                
                # Extract price text and clean it
                price_text = price_elem.text.strip() if price_elem else "0"
                
                # Clean price text (remove currency symbols and formatting)
                price_text = price_text.replace("Rs.", "").replace("PKR", "").replace("₨", "").replace(",", "").strip()
                
                # Extract numeric price value
                try:
                    # Find all numbers in the text
                    number_matches = re.findall(r'\d+\.?\d*', price_text)
                    if number_matches:
                        product_data['price'] = float(number_matches[0])
                    else:
                        product_data['price'] = 0
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing price '{price_text}': {e}")
                    product_data['price'] = 0
                
                # ---- Extract product image URL ----
                img_elem = card.select_one('img.groceries-image')
                if not img_elem:
                    img_elem = card.select_one('img')
                    
                if img_elem and img_elem.has_attr('src'):
                    product_data['image_url'] = img_elem['src']
                elif img_elem and img_elem.has_attr('data-src'):
                    product_data['image_url'] = img_elem['data-src']
                else:
                    product_data['image_url'] = ""
                
                # Source website
                product_data['source'] = 'foodpanda.pk'
                
                # Foodpanda doesn't typically show ratings in search results
                product_data['rating'] = 0
                product_data['reviews_count'] = 0
                
                # Generate a hash of the product to avoid duplicates
                product_hash = hashlib.md5(f"{product_data['name']}|{product_data['price']}".encode()).hexdigest()
                if product_hash in self.processed_product_hashes:
                    logger.debug(f"Skipping duplicate product: {product_data['name']}")
                    continue
                self.processed_product_hashes.add(product_hash)
                
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
                
                page_product_count += 1
                total_products += 1
                
            except Exception as e:
                logger.error(f"Error processing Foodpanda product card: {e}")
                # Log full traceback for debugging
                logger.error(traceback.format_exc())
        
        logger.info(f"Extracted {page_product_count} products from Foodpanda page {page}")
        
        # If we got no products, we might have reached the last page
        if page_product_count == 0:
            logger.info(f"No products found on page {page}, stopping pagination")
            break
    
    logger.info(f"Total extracted {total_products} products from Foodpanda across {min(page, max_pages)} pages")
