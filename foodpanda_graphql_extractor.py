import asyncio
import json
import os
import time
from datetime import datetime
import requests
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of cities to search for Pandamart
CITIES = [
    "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
    "Multan", "Peshawar", "Hyderabad", "Gujranwala", "Sialkot",
    "Quetta", "Abbottabad", "Sukkur", "Larkana", "Sheikhupura"
]

class FoodpandaGraphQLExtractor:
    """Class to extract coffee product data from Foodpanda using GraphQL API"""
    
    def __init__(self, cities=None, headless=True, save_dir="data/raw", cache_duration_hours=24):
        self.cities = cities or CITIES
        self.headless = headless
        self.save_dir = save_dir
        self.cache_duration_hours = cache_duration_hours
        self.cache_dir = os.path.join(save_dir, "cache")
        self.vendor_ids = {}
        
        # Ensure directories exist
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_path(self, key):
        """Generate a cache file path based on a key"""
        cache_filename = f"{key.replace('/', '_').replace(':', '_')}.json"
        return os.path.join(self.cache_dir, cache_filename)
    
    def get_from_cache(self, key):
        """Get data from cache if it exists and is not expired"""
        cache_path = self.get_cache_path(key)
        
        if os.path.exists(cache_path):
            # Check if cache is still valid (not expired)
            cache_time = os.path.getmtime(cache_path)
            current_time = time.time()
            if (current_time - cache_time) / 3600 < self.cache_duration_hours:
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        logger.info(f"Using cached data for {key}")
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading cache: {e}")
        
        return None
    
    def save_to_cache(self, key, data):
        """Save data to cache"""
        cache_path = self.get_cache_path(key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error writing to cache: {e}")
    
    async def discover_pandamart_vendors(self):
        """
        Discover Pandamart vendor IDs across different cities in Pakistan using Playwright
        """
        # Check if we have vendor IDs in cache
        vendors_cache_key = "pandamart_vendor_ids"
        cached_vendors = self.get_from_cache(vendors_cache_key)
        if cached_vendors:
            logger.info(f"Using cached vendor IDs for {len(cached_vendors)} cities")
            self.vendor_ids = cached_vendors
            return cached_vendors
        
        logger.info("Starting discovery of Pandamart vendors across cities")
        vendor_ids = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                await page.goto("https://www.foodpanda.pk/", timeout=60000)
                
                for city in self.cities:
                    try:
                        logger.info(f"Searching for Pandamart in {city}...")
                        
                        # Navigate and select location                        try:
                            # Increase timeout and try different selectors
                            await page.wait_for_load_state("networkidle", timeout=10000)
                            
                            # Try all possible selectors with longer timeouts
                            try:
                                await page.click('text=Change location', timeout=10000)
                                logger.info(f"Found 'Change location' text in {city}")
                            except Exception:
                                try:
                                    await page.click('[data-testid="location-panel-change-location"]', timeout=10000)
                                    logger.info(f"Found location panel in {city}")
                                except Exception:
                                    try:
                                        await page.click('button:has-text("Change")', timeout=10000)
                                        logger.info(f"Found 'Change' button in {city}")
                                    except Exception:
                                        # Last resort - try to find by XPath
                                        logger.info(f"Trying XPath selectors for {city}")
                                        await page.click('//button[contains(., "Change")]', timeout=10000)
                          # Enter city name and wait longer for suggestions
                        await page.fill('input[placeholder="Enter your delivery address"]', city)
                        await page.wait_for_timeout(5000)  # Give more time for suggestions to appear
                        
                        # Click first suggestion
                        await page.keyboard.press("ArrowDown")
                        await page.keyboard.press("Enter")
                        await page.wait_for_load_state("networkidle", timeout=45000)  # Increased timeout
                          # Search for Pandamart with increased wait times
                        logger.info(f"Looking for search box in {city}...")
                        try:
                            # Try using multiple selectors for the search box
                            search_box = await page.wait_for_selector('input[type="search"], input[placeholder*="search"], [data-testid*="search"]', timeout=10000)
                            if search_box:
                                await search_box.fill("pandamart")
                                await page.keyboard.press("Enter")
                                await page.wait_for_timeout(10000)  # Increased wait time after search
                                logger.info(f"Search for Pandamart submitted in {city}")
                            else:
                                logger.warning(f"No search box found in {city}")
                                continue
                        except Exception as search_error:
                            logger.warning(f"Error finding search box in {city}: {search_error}")
                            continue
                          # Find Pandamart vendor with improved detection logic
                        logger.info(f"Looking for Pandamart links in {city}...")
                        try:
                            # Wait for results to load
                            await page.wait_for_load_state("networkidle", timeout=15000)
                            
                            # Try different selectors to find Pandamart links
                            links = []
                            
                            # Method 1: By text content
                            try:
                                links = await page.locator('a:has-text("pandamart"), a:has-text("Pandamart")').all()
                                if links:
                                    logger.info(f"Found {len(links)} Pandamart links by text in {city}")
                            except Exception as e:
                                logger.warning(f"Error finding links by text: {e}")
                            
                            # Method 2: By URL pattern if Method 1 failed
                            if not links:
                                try:
                                    links = await page.locator('a[href*="pandamart"]').all()
                                    if links:
                                        logger.info(f"Found {len(links)} Pandamart links by URL in {city}")
                                except Exception as e:
                                    logger.warning(f"Error finding links by URL: {e}")
                            
                            # Process found link
                            if links:
                                url = await links[0].get_attribute("href")
                                if url:
                                    # Extract vendor ID from URL (like /sx92/pandamart)
                                    parts = url.split("/")
                                    vendor_id = parts[2] if len(parts) > 2 else "Not found"
                                    vendor_ids[city] = vendor_id
                                    logger.info(f"Found vendor ID for {city}: {vendor_id}")
                                else:
                                    logger.warning(f"No href found for Pandamart in {city}")
                            else:
                                # Take a screenshot for debugging
                                await page.screenshot(path=f"{city}_pandamart_search.png")
                                logger.warning(f"No Pandamart found in {city}, saved screenshot")
                      except Exception as e:
                        logger.error(f"Error in {city}: {str(e)}")
                        # Save a screenshot for debugging
                        try:
                            await page.screenshot(path=f"{city}_error.png")
                            logger.info(f"Error screenshot saved for {city}")
                        except:
                            pass
                        # Continue with next city
                
            finally:
                await browser.close()
        
        # Save vendor IDs to cache
        if vendor_ids:
            self.vendor_ids = vendor_ids
            self.save_to_cache(vendors_cache_key, vendor_ids)
        
        return vendor_ids
    
    def fetch_coffee_products_via_graphql(self, vendor_id, city):
        """
        Fetch coffee products from a Pandamart vendor using the Foodpanda GraphQL API
        """
        # Check if we have products in cache for this vendor
        cache_key = f"coffee_products_{city}_{vendor_id}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        logger.info(f"Fetching coffee products from {city} (vendor: {vendor_id})...")
        
        # GraphQL endpoint
        url = "https://www.foodpanda.pk/gql"
        
        # GraphQL query for searching products
        query = """
        query vendorSearchProduct($clientName: String!, $vendorId: String!, $sortOrder: VendorSort, $query: String!) {
          vendor(id: $vendorId) {
            id
            name
            searchProducts(sortOrder: $sortOrder, query: $query, limit: 50) {
              name
              id
              imageUrl
              description
              price {
                code
                value
                fractional
                formatted
              }
              discountedPrice {
                code
                value
                fractional
                formatted
              }
              purchasable
              maximumOrderQuantity
              minimumOrderQuantity
              productTags {
                id
                label
                labelColor
                color
              }
            }
          }
        }
        """
        
        # Variables for the GraphQL query
        variables = {
            "clientName": "web",
            "vendorId": vendor_id,
            "sortOrder": "PRICE_ASC",
            "query": "coffee"  # Search for coffee products
        }
        
        # Headers for the request
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Make the request
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"query": query, "variables": variables}
            )
            
            data = response.json()
            
            if "data" in data and data["data"]["vendor"] and data["data"]["vendor"]["searchProducts"]:
                products = data["data"]["vendor"]["searchProducts"]
                logger.info(f"Found {len(products)} coffee products in {city}")
                
                result = {
                    "city": city,
                    "vendor_id": vendor_id,
                    "products": products,
                    "scraped_at": datetime.now().isoformat()
                }
                
                # Save to cache
                self.save_to_cache(cache_key, result)
                
                return result
            else:
                logger.warning(f"No products found or error in response for {city}")
                return None
                
        except Exception as e:
            logger.error(f"API request error for {city}: {str(e)}")
            return None
    
    def transform_to_standard_format(self, graphql_data):
        """
        Transform GraphQL API data to the standard format used by the coffee market data collector
        """
        standard_products = []
        
        for city_data in graphql_data:
            if not city_data:
                continue
                
            city = city_data.get("city", "Unknown")
            products = city_data.get("products", [])
            
            for product in products:
                # Skip non-coffee products
                if not self._is_coffee_product(product.get("name", "")):
                    continue
                    
                price_value = 0
                if "price" in product and "value" in product["price"]:
                    price_value = float(product["price"]["value"])
                
                # Create standardized product data
                standard_product = {
                    "id": product.get("id", ""),
                    "name": product.get("name", "Unknown"),
                    "scraped_at": datetime.now().isoformat(),
                    "price": price_value,
                    "image_url": product.get("imageUrl", ""),
                    "product_url": f"https://www.foodpanda.pk/darkstore/{city_data.get('vendor_id', '')}/product/{product.get('id', '')}",
                    "source": f"foodpanda.pk ({city})",
                    "city": city,
                    "description": product.get("description", ""),
                    "brand": self._extract_brand(product.get("name", "")),
                }
                
                # Add additional categorization
                standard_product["type"] = self._extract_coffee_type(standard_product["name"])
                standard_product["packaging"] = self._extract_packaging_info(standard_product["name"])
                standard_product["price_tier"] = self._get_price_tier(standard_product["price"])
                
                standard_products.append(standard_product)
        
        return standard_products
    
    def _is_coffee_product(self, name):
        """
        Check if a product name indicates a coffee product.
        """
        name_lower = name.lower()
        coffee_keywords = ['coffee', 'café', 'cafe', 'espresso', 'cappuccino', 'latte', 'mocha', 
                          'americano', 'nescafe', 'folgers', 'lavazza', 'illy', 'maxwell', 
                          'starbucks', 'arabica', 'robusta']
        
        # Check if any of the coffee keywords are in the product name
        for keyword in coffee_keywords:
            if keyword in name_lower:
                # Exclude non-coffee products that might contain coffee keywords
                exclusion_keywords = ['mug', 'cup', 'table', 'creamer', 'machine', 'maker', 'filter']
                for exclusion in exclusion_keywords:
                    if exclusion in name_lower and 'coffee ' + exclusion in name_lower:
                        return False
                return True
        
        return False
    
    def _extract_brand(self, name):
        """
        Extract brand name from product name.
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
    
    def _extract_coffee_type(self, name):
        """
        Extract coffee type from product name.
        """
        name_lower = name.lower()
        
        # Determine coffee type based on keywords
        if any(term in name_lower for term in ['instant', 'classic', 'gold']):
            return 'instant'
        elif any(term in name_lower for term in ['ground', 'filter']):
            return 'ground'
        elif any(term in name_lower for term in ['bean', 'whole']):
            return 'beans'
        elif any(term in name_lower for term in ['capsule', 'pod']):
            return 'capsule/pod'
        elif any(term in name_lower for term in ['3 in 1', '3in1', '2 in 1', '2in1']):
            return 'coffee mix'
        
        return 'other'
    
    def _extract_packaging_info(self, name):
        """
        Extract packaging information from product name.
        """
        import re
        
        packaging_info = {
            'value': 0,
            'unit': 'unknown',
            'display': 'unknown'
        }
        
        # Look for common packaging patterns
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
    
    def _get_price_tier(self, price):
        """
        Get price tier based on price value.
        """
        if price == 0:
            return 'unknown'
        elif price < 1000:
            return 'economy'
        elif price < 2500:
            return 'mid-range'
        else:
            return 'premium'
    
    async def collect_data(self):
        """
        Collect coffee product data from all Pandamart vendors
        """
        logger.info("Starting collection of coffee product data from Pandamart vendors via GraphQL API")
        
        start_time = time.time()
        
        # Step 1: Discover Pandamart vendors across cities
        vendor_ids = await self.discover_pandamart_vendors()
        
        if not vendor_ids:
            logger.warning("No Pandamart vendors found")
            return []
        
        logger.info(f"Found {len(vendor_ids)} Pandamart vendors across different cities")
        
        # Step 2: Fetch coffee products for each vendor
        all_coffee_data = []
        
        for city, vendor_id in vendor_ids.items():
            coffee_data = self.fetch_coffee_products_via_graphql(vendor_id, city)
            if coffee_data:
                all_coffee_data.append(coffee_data)
            # Wait between requests to avoid rate limiting
            time.sleep(1)
        
        # Step 3: Transform to standard format
        logger.info("Transforming data to standard format")
        standard_products = self.transform_to_standard_format(all_coffee_data)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Collected {len(standard_products)} coffee products from {len(all_coffee_data)} cities in {elapsed_time:.2f} seconds")
        
        return standard_products
    
    def save_data(self, products, timestamp=None):
        """
        Save collected data to files
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data
        raw_file = os.path.join(self.save_dir, f"foodpanda_graphql_results_{timestamp}.json")
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(products)} products to {raw_file}")
        return raw_file

async def main():
    # Create the extractor
    extractor = FoodpandaGraphQLExtractor(
        headless=False,  # Set to True for production
        save_dir="data/raw"
    )
    
    # Collect the data
    products = await extractor.collect_data()
    
    # Save the data
    if products:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = extractor.save_data(products, timestamp)
        
        logger.info(f"Data collection complete")
        logger.info(f"Collected {len(products)} products from {len(extractor.vendor_ids)} cities")
        logger.info(f"Data saved to {output_file}")
    else:
        logger.warning("No products collected")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
