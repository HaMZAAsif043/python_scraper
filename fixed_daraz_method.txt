    def extract_daraz_data(self, max_pages=3):
        """
        Extract coffee product data from Daraz.
        
        Args:
            max_pages (int): Maximum number of pages to scrape
        """
        logger.info("Extracting coffee data from Daraz")
        
        # Make sure we're passing a string URL
        base_url = self.target_websites['daraz']['search_url']
        if not isinstance(base_url, str):
            logger.warning(f"Daraz URL is not a string: {type(base_url)}")
            return
        
        total_products = 0
        
        # Process multiple pages
        for page in range(1, max_pages + 1):
            # Generate URL for current page (page 1 uses the base URL)
            current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'daraz')
            logger.info(f"Processing Daraz page {page} with URL: {current_url}")
            
            soup = self.get_page_content(current_url, use_selenium=True)
            
            if not soup:
                logger.warning(f"Failed to get Daraz content for page {page}")
                break
            
            # Save HTML for debugging (only for first page)
            if page == 1:
                with open("daraz_debug.html", "w", encoding="utf-8") as f:
                    f.write(str(soup))
            
            logger.info(f"Trying to find Daraz products on page {page} with primary selector")
            
            # Extract product items using the specified CSS selector
            product_selector = self.target_websites['daraz']['product_selector']
            product_cards = soup.select(product_selector)
            
            if not product_cards:
                logger.warning(f"No product cards found on Daraz page {page} using selector: {product_selector}")
                # Try alternative selectors from the configuration
                alternative_selectors = self.target_websites['daraz']['alternative_selectors']['product_selector']
                for selector in alternative_selectors:
                    logger.info(f"Trying alternative product selector for Daraz: {selector}")
                    product_cards = soup.select(selector)
                    if product_cards:
                        logger.info(f"Found {len(product_cards)} products using alternative selector: {selector}")
                        break
            else:
                logger.info(f"Found {len(product_cards)} products using primary selector on page {page}")
            
            if not product_cards:
                logger.warning(f"Failed to find any products with all selectors for Daraz on page {page}")
                continue
            
            logger.info(f"Processing {len(product_cards)} product cards from Daraz page {page}")
            page_product_count = 0
            
            for card in product_cards:
                try:
                    product_data = {}
                    
                    # Extract name using the specific selector from configuration
                    name_selector = self.target_websites['daraz']['name_selector']
                    name_elem = card.select_one(name_selector)
                
                    if not name_elem:
                        logger.debug(f"Name not found with primary selector: {name_selector}")
                        # Try alternative selectors if main selector fails
                        for selector in self.target_websites['daraz']['alternative_selectors']['name_selector']:
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
                    price_selector = self.target_websites['daraz']['price_selector']
                    price_elem = card.select_one(price_selector)
                    if not price_elem:
                        # Try some common price selectors
                        price_elem = card.select_one('.price')
                        if not price_elem:
                            price_elem = card.select_one('[data-price]')
                    
                    price_text = price_elem.text.strip() if price_elem else "0"
                    # Clean price text (remove "Rs. " and commas)
                    price_text = price_text.replace("Rs.", "").replace(",", "").replace("PKR", "").strip()
                    try:
                        product_data['price'] = float(price_text)
                    except ValueError:
                        product_data['price'] = 0
                    
                    # Extract rating
                    rating_elem = card.select_one('.rating--b2Qtx')
                    product_data['rating'] = float(rating_elem.text.strip()) if rating_elem else 0
                    
                    # Extract number of reviews
                    reviews_elem = card.select_one('.rating__review--ygkUy')
                    reviews_text = reviews_elem.text.strip() if reviews_elem else "0"
                    # Extract the number from text like "(120)"
                    reviews_count = ''.join(filter(str.isdigit, reviews_text))
                    product_data['reviews_count'] = int(reviews_count) if reviews_count else 0
                    
                    # Source website
                    product_data['source'] = 'daraz.pk'
                    
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
                    
                    # Increment page counter
                    page_product_count += 1
                    total_products += 1
                    
                except Exception as e:
                    logger.error(f"Error processing Daraz product card on page {page}: {e}")
            
            logger.info(f"Extracted {page_product_count} products from Daraz page {page}")
            
            # If we got fewer products than expected, we might have reached the last page
            if page_product_count == 0:
                logger.info(f"No products found on page {page}, stopping pagination")
                break
        
        logger.info(f"Total extracted {total_products} products from Daraz across {min(page, max_pages)} pages")
