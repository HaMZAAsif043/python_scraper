def extract_foodpanda_data(self, max_pages=3):
    """
    Extract coffee product data from Foodpanda/Pandamart.
    
    Args:
        max_pages (int): Maximum number of pages to scrape
    """
    logger.info("Extracting coffee data from Foodpanda")
    
    base_url = self.target_websites['foodpanda']['search_url']
    if not isinstance(base_url, str):
        logger.warning(f"Foodpanda URL is not a string: {type(base_url)}")
        return
        
    total_products = 0
    
    # Process multiple pages
    for page in range(1, max_pages + 1):
        # Generate URL for current page
        current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'foodpanda')
        logger.info(f"Processing Foodpanda page {page} with URL: {current_url}")
        
        # Use Selenium to load dynamic content
        soup = self.get_page_content(current_url, use_selenium=True)
        
        if not soup:
            logger.warning(f"Failed to get Foodpanda content for page {page}")
            break
        
        # For debugging purposes, save the first page's HTML
        if page == 1:
            with open("foodpanda_debug.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
        
        # Get product cards from the page using the configured selector
        product_selector = self.target_websites['foodpanda']['product_selector']
        product_cards = soup.select(product_selector)
        
        # If no products found with the primary selector, try alternatives
        if not product_cards and 'alternative_selectors' in self.target_websites['foodpanda']:
            logger.warning(f"No product cards found on Foodpanda page {page} using selector: {product_selector}")
            for alt_selector in self.target_websites['foodpanda']['alternative_selectors'].get('product_selector', []):
                product_cards = soup.select(alt_selector)
                if product_cards:
                    logger.info(f"Found products with alternative selector: {alt_selector}")
                    break
        
        # If still no products found, try a more generic selector
        if not product_cards:
            logger.warning("Still no product cards found, trying generic selector")
            product_cards = soup.select('ul.product-grid > li')
            
        # If still no products found, try one last generic approach
        if not product_cards:
            logger.warning("Trying one more generic approach for Pandamart product grid")
            product_cards = soup.select('.groceries-products-list .dish-card')
            
        if not product_cards:
            logger.warning(f"No product cards found on Foodpanda page {page}, stopping pagination")
            break
        
        logger.info(f"Found {len(product_cards)} product cards on Foodpanda page {page}")
        page_product_count = 0
        
        # Process each product card
        for card in product_cards:
            try:
                product_data = {
                    'id': f"foodpanda_{time.time()}_{total_products}",
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Extract product name
                name_selector = self.target_websites['foodpanda']['name_selector']
                name_elem = card.select_one(name_selector)
                
                # Try alternative name selectors if main one fails
                if not name_elem and 'alternative_selectors' in self.target_websites['foodpanda']:
                    for selector in self.target_websites['foodpanda']['alternative_selectors'].get('name_selector', []):
                        name_elem = card.select_one(selector)
                        if name_elem:
                            logger.debug(f"Found name using alternative selector: {selector}")
                            break
                
                # Try one more selector specific to Pandamart structure
                if not name_elem:
                    name_elem = card.select_one('.groceries-product-card-name')
                    
                if name_elem:
                    product_data['name'] = name_elem.text.strip()
                    logger.debug(f"Extracted product name: {product_data['name']}")
                else:
                    logger.warning("Could not find product name with any selector")
                    product_data['name'] = "Unknown"
                
                # Skip non-coffee products
                if not self._is_coffee_product(product_data['name']):
                    logger.debug(f"Skipping non-coffee product: {product_data['name']}")
                    continue
                
                # Extract price
                price_selector = self.target_websites['foodpanda']['price_selector']
                price_elem = card.select_one(price_selector)
                
                # Try alternative price selectors if main one fails
                if not price_elem and 'alternative_selectors' in self.target_websites['foodpanda']:
                    for selector in self.target_websites['foodpanda']['alternative_selectors'].get('price_selector', []):
                        price_elem = card.select_one(selector)
                        if price_elem:
                            break
                
                # Try one more selector specific to Pandamart structure
                if not price_elem:
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
                
                # Extract image URL
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
        
        logger.info(f"Extracted {page_product_count} products from Foodpanda page {page}")
        
        # If we got fewer products than expected, we might have reached the last page
        if page_product_count == 0:
            logger.info(f"No products found on page {page}, stopping pagination")
            break
    
    logger.info(f"Total extracted {total_products} products from Foodpanda across {min(page, max_pages)} pages")
