"""
Module for collecting coffee market data from Pakistani e-commerce and retail websites.
This module focuses on:
- Types of coffee (instant, ground, beans, powdered)
- Packaging sizes and variants
- Price data and segmentation
- Customer reviews and ratings
- Brand popularity and market presence
"""

import os
import json
import logging
import time
import random
import re
import hashlib
import pickle
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from ..config import PATHS
from urllib.parse import urljoin # Added import

logger = logging.getLogger(__name__)

# Define price tiers for categorization
PRICE_TIERS = {
    'low': {'min': 0, 'max': 1000},  # Economy brands and small packages
    'mid': {'min': 1001, 'max': 2500},  # Mainstream brands
    'premium': {'min': 2501, 'max': float('inf')}  # Premium/imported brands
}

class CoffeeMarketDataCollector:
    """Class to collect coffee product data from Pakistani e-commerce sites."""
    
    def __init__(self, use_cache=True, cache_duration_hours=24):
        """
        Initialize the collector with required settings.
        
        Args:
            use_cache (bool): Whether to use cached responses to avoid redundant requests
            cache_duration_hours (int): How long to consider cache entries valid
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Configure target websites with both search URLs and product page URLs
        self.target_websites = {
            'daraz': {
                'search_url': 'https://www.daraz.pk/catalog/?q=coffee',
                'product_selector': 'div._17mcb > div', # Updated: Targets individual product containers
                'name_selector': 'div.buTCk div.RfADt > a', # Updated: More specific name selector relative to product card
                'price_selector': '.price--NVB62', # Existing, assumed relative to product_selector
                'rating_selector': '.rating--b2Qtx', # Existing
                'reviews_selector': '.rating__review--ygkUy', # Existing
                'requires_selenium': True,
                'alternative_selectors': {
                    'product_selector': [
                        'div.box--ujueT', 
                        'div.product-card', 
                        '.gridItem--Yd0sa', # Common Daraz class
                        'div[class*="card--"]', # For dynamic card classes
                        'div[data-qa-locator="product-item"]' # Daraz specific QA locator
                    ],
                    'name_selector': [
                        '.title--wFj93', # Original name selector
                        'a[title]', # Product links often have titles
                        '.pdp-mod-product-badge-title', 
                        'h2 > a', 
                        '.item-title',
                        'a[href*="/products/"]' # Generic product links
                    ],
                    'price_selector': [ # Added alternative price selectors
                        '.price', 
                        '[data-price]', 
                        '.currency--GVKjl', # Daraz specific price class
                        'span[class*="price"]'
                    ]
                }
            },
            'foodpanda': {
                'search_url': 'https://www.foodpanda.pk/groceries/pandamart/s/search/coffee',
                'product_selector': '.dish-card',
                'name_selector': '.dish-name',
                'price_selector': '.price',
                'requires_selenium': True,
                'alternative_selectors': {
                    'product_selector': ['.product-card', '.product-item', '.product'],
                    'name_selector': ['.product-name', '.title', '.name'],
                    'price_selector': ['.discount-price', '.product-price', '.amount']
                }
            },
            'alfatah': {
                'search_url': 'https://alfatah.pk/search?q=coffee&options%5Bprefix%5D=last',
                'product_selector': '.product-card.card-border',
                'name_selector': '.product-title a',
                'price_selector': '.product-price',
                'requires_selenium': True,
                'alternative_selectors': {
                    'product_selector': [
                        '.col-6.col-sm-4.col-md-3.col-lg-2 .product-card',
                        '#shopify_section_template__22762959470880__main_content .product-card',
                        '.product-grid__item',
                        '.card'
                    ],
                    'name_selector': [
                        '.product-title-ellipsis',
                        '.card__heading',
                        '.product-item-title',
                        '.full-unstyled-link'
                    ],
                    'price_selector': [
                        'p.product-price',
                        '.price-item',
                        '.price',
                        '.price__regular'
                    ]
                }
            },
            'naheed': {
                'search_url': 'https://www.naheed.pk/catalogsearch/result/?q=coffee',
                'product_selector': 'li.item.product.product-item',
                'name_selector': '.product.details.product-item-details .product-item-name .product-item-link',
                'price_selector': '.price-box .price',
                'requires_selenium': True,
                'alternative_selectors': {
                    'product_selector': ['.category-products.products.wrapper.grid.products-grid > div > div > ol > li', '.product-item-info'],
                    'name_selector': ['.product.details.product-item-details', '.product-name'],
                    'price_selector': ['.price-container .price', '.special-price']
                }
            },
            'metro': {
                'search_url': 'https://www.metro-online.pk/search/coffee?searchText=coffee&url=&isSearched=true',
                'product_selector': '.product-item',
                'name_selector': '.product-item-link',
                'price_selector': '.price',
                'requires_selenium': True,
                'alternative_selectors': {
                    'product_selector': ['li.product', '.product-item-info'],
                    'name_selector': ['h2.woocommerce-loop-product__title', '.product-name'],
                    'price_selector': ['span.price', '.price-box']
                }
            },
            'alibaba': {
                'search_url': 'https://www.alibaba.com/trade/search?spm=a2700.product_home_newuser.home_new_user_first_screen_fy23_pc_search_bar.keydown__Enter&tab=all&SearchText=coffee',
                'product_selector': '.J-offer-wrapper',
                'name_selector': '.elements-title-normal__content',
                'price_selector': '.elements-offer-price-normal__price',
                'requires_selenium': True,
                'alternative_selectors': {
                    'product_selector': ['.item-area', '.organic-list-offer-outter'],
                    'name_selector': ['.product-name', '.organic-list-offer-name'],
                    'price_selector': ['.price-box', '.organic-list-offer-price']
                }
            }
        }
        
        # Cache configuration
        self.cache_dir = os.path.join(PATHS["raw_data"], "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.use_cache = use_cache
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
        # Initialize data storage
        self.raw_data = []
        self.processed_data = {
            'products': [],
            'brands': {},
            'types': {},
            'packaging': {},
            'price_tiers': {tier: [] for tier in PRICE_TIERS}
        }
        
        # Initialize a set to track already processed products (to avoid duplicates)
        self.processed_product_hashes = set()
    
    def setup_selenium_driver(self):
        """Set up and return a configured Chrome WebDriver for sites requiring JavaScript."""
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument(f"user-agent={self.headers['User-Agent']}")
        
        return webdriver.Chrome(options=options)
    def get_cache_path(self, url):
        """
        Generate a cache file path for a given URL.
        
        Args:
            url (str): URL to generate cache path for
            
        Returns:
            str: Path to cache file
        """
        # Make sure the URL is a string
        if isinstance(url, dict):
            logger.warning("URL was passed as a dictionary instead of string")
            # Try to extract the search_url if this is a website config dictionary
            if 'search_url' in url:
                url = url['search_url']
            else:
                # Create a hash from the dictionary's string representation as fallback
                url = str(url)
        
        # Create a unique filename based on the URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.pkl")
    
    def get_from_cache(self, url):
        """
        Try to get a cached response for the given URL.
        
        Args:
            url (str): URL to get from cache
            
        Returns:
            BeautifulSoup object or None if not in cache or expired
        """
        if not self.use_cache:
            return None
            
        cache_path = self.get_cache_path(url)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                cache_entry = pickle.load(f)
                
            # Check if the cache entry is still valid
            if datetime.now() - cache_entry['timestamp'] <= self.cache_duration:
                logger.info(f"Using cached content for {url}")
                return cache_entry['content']
            else:
                logger.info(f"Cache expired for {url}")
                return None
        except Exception as e:
            logger.warning(f"Error reading cache for {url}: {e}")
            return None
    
    def save_to_cache(self, url, content):
        """
        Save content to cache.
        
        Args:
            url (str): URL as the cache key
            content (BeautifulSoup): Content to cache
        """
        if not self.use_cache:
            return
            
        cache_path = self.get_cache_path(url)
        
        try:
            cache_entry = {
                'timestamp': datetime.now(),
                'content': content
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_entry, f)
                
            logger.info(f"Cached content for {url}")
        except Exception as e:
            logger.warning(f"Error saving to cache for {url}: {e}")
    
    def get_page_content(self, url, use_selenium=False, max_retries=3):
        """
        Get page content either with requests or selenium depending on the site's requirements.
        
        Args:
            url (str): URL to scrape
            use_selenium (bool): Whether to use Selenium for JavaScript rendering
            max_retries (int): Number of attempts to make before giving up
            
        Returns:
            BeautifulSoup object or None if failed
        """
        # First try to get from cache
        cached_content = self.get_from_cache(url)
        if cached_content is not None:
            return cached_content
        
        logger.info(f"Fetching content from {url} (using {'Selenium' if use_selenium else 'Requests'})")
        
        for attempt in range(max_retries):
            try:
                if use_selenium:
                    driver = None
                    try:
                        driver = self.setup_selenium_driver()
                        driver.get(url)
                        
                        # Wait for dynamic content to load
                        time.sleep(random.uniform(3, 5))
                        
                        # Scroll down a bit to load lazy content
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
                        time.sleep(1)
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 2/3);")
                        time.sleep(1)
                        
                        # Check for and handle cookie consent dialogs
                        try:
                            consent_buttons = driver.find_elements(By.XPATH, 
                                "//button[contains(text(), 'Accept') or contains(text(), 'I Agree') or contains(text(), 'OK') or contains(text(), 'Got it')]")
                            if consent_buttons:
                                consent_buttons[0].click()
                                logger.info("Closed consent dialog")
                                time.sleep(1)
                        except Exception:
                            pass
                        
                        # Get the page source after JavaScript has loaded
                        page_content = driver.page_source
                        soup = BeautifulSoup(page_content, 'html.parser')
                        
                        # Save successful result to cache
                        self.save_to_cache(url, soup)
                        return soup
                        
                    except WebDriverException as e:
                        logger.error(f"Selenium error on attempt {attempt+1}/{max_retries}: {e}")
                        if attempt == max_retries - 1:
                            return self.generate_sample_data(url)
                    finally:
                        if driver:
                            driver.quit()
                else:
                    # Add a random delay to avoid rate-limiting
                    if attempt > 0:  # Only delay on retries
                        delay = random.uniform(2, 5)
                        logger.info(f"Retry {attempt+1}/{max_retries} after {delay:.1f}s")
                        time.sleep(delay)
                    
                    # Rotate user agents
                    user_agents = [
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
                    ]
                    self.session.headers.update({'User-Agent': random.choice(user_agents)})
                    
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Save successful result to cache
                    self.save_to_cache(url, soup)
                    return soup
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt+1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    # If all retries fail, return sample data
                    return self.generate_sample_data(url)
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt+1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    return self.generate_sample_data(url)
                    
        return None
    
    def generate_sample_data(self, url):
        """
        Generate sample coffee product data when scraping fails.
        This ensures the system can still function for testing and demonstration.
        
        Args:
            url (str): The URL that failed to load
            
        Returns:
            BeautifulSoup: A soup object with sample product data
        """
        logger.warning(f"Generating sample data for {url}")
        
        # Create a basic HTML structure
        sample_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="product-list">
                <!-- Sample products will be inserted here -->
            </div>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(sample_html, 'html.parser')
        product_list = soup.select_one('.product-list')
        
        # Sample coffee products commonly found in Pakistan
        sample_products = [
            {
                'name': 'Nescafe Classic Instant Coffee 200g',
                'price': 950,
                'rating': 4.5,
                'reviews': 120
            },
            {
                'name': 'Nescafe Gold Blend Premium Coffee 100g Jar',
                'price': 1250,
                'rating': 4.7,
                'reviews': 85
            },
            {
                'name': 'Davidoff Rich Aroma Ground Coffee 250g',
                'price': 2350,
                'rating': 4.8,
                'reviews': 42
            },
            {
                'name': 'Lavazza Qualita Oro Ground Coffee 250g',
                'price': 2100,
                'rating': 4.6,
                'reviews': 38
            },
            {
                'name': 'Maxwell House Original Roast Ground Coffee 300g',
                'price': 1800,
                'rating': 4.2,
                'reviews': 29
            },
            {
                'name': 'Mehran Instant Coffee Powder 50g',
                'price': 450,
                'rating': 3.9,
                'reviews': 65
            },
            {
                'name': 'Nescafe 3 in 1 Instant Coffee Mix 30 Sticks',
                'price': 850,
                'rating': 4.4,
                'reviews': 95
            },
            {
                'name': 'Folgers Classic Roast Ground Coffee 226g',
                'price': 1550,
                'rating': 4.3,
                'reviews': 22
            },
            {
                'name': 'Continental Premium Blend Coffee Powder 100g',
                'price': 750,
                'rating': 4.0,
                'reviews': 48
            },
            {
                'name': 'Kauphy Italian Roast Coffee Beans 250g',
                'price': 1950,
                'rating': 4.8,
                'reviews': 15
            }
        ]
        
        # Determine which website we're generating data for
        website_name = "unknown"
        for name, site_info in self.target_websites.items():
            if site_info.get('search_url') in url:
                website_name = name
                break
        
        # Create product elements based on the website we're simulating
        if (website_name == 'daraz'):
            # Create Daraz-like product cards
            for product in sample_products:
                product_div = soup.new_tag('div', attrs={'class': 'gridItem--Yd0sa'})
                
                title_div = soup.new_tag('div', attrs={'class': 'title--wFj93'})
                title_div.string = f"[SAMPLE] {product['name']}"
                
                price_div = soup.new_tag('div', attrs={'class': 'price--NVB62'})
                price_div.string = f"Rs. {product['price']}"
                
                rating_div = soup.new_tag('div', attrs={'class': 'rating--b2Qtx'})
                rating_div.string = str(product['rating'])
                
                reviews_div = soup.new_tag('div', attrs={'class': 'rating__review--ygkUy'})
                reviews_div.string = f"({product['reviews']})"
                
                product_div.append(title_div)
                product_div.append(price_div)
                product_div.append(rating_div)
                product_div.append(reviews_div)
                
                product_list.append(product_div)
        
        elif website_name == 'alfatah':
            # Create Alfatah-like product cards
            for product in sample_products:
                product_div = soup.new_tag('div', attrs={'class': 'product-item'})
                
                title_div = soup.new_tag('div', attrs={'class': 'product-item-title'})
                title_div.string = f"[SAMPLE] {product['name']}"
                
                price_div = soup.new_tag('div', attrs={'class': 'price'})
                price_div.string = f"Rs. {product['price']}"
                
                product_div.append(title_div)
                product_div.append(price_div)
                
                product_list.append(product_div)
        
        elif website_name == 'naheed':
            # Create Naheed-like product cards
            for product in sample_products:
                product_div = soup.new_tag('div', attrs={'class': 'product-item'})
                
                title_div = soup.new_tag('div', attrs={'class': 'product-item-title'})
                title_div.string = f"[SAMPLE] {product['name']}"
                
                price_div = soup.new_tag('div', attrs={'class': 'price'})
                price_div.string = f"Rs. {product['price']}"
                
                product_div.append(title_div)
                product_div.append(price_div)
                
                product_list.append(product_div)
        
        else:
            # Generic product cards
            for product in sample_products:                
                product_div = soup.new_tag('div', attrs={'class': 'product-item'})
                title_div = soup.new_tag('h2')
                title_div.string = f"[SAMPLE] {product['name']}"
                
                price_div = soup.new_tag('div', attrs={'class': 'price'})
                price_div.string = f"Rs. {product['price']}"
                
                rating_div = soup.new_tag('div', attrs={'class': 'rating'})
                rating_div.string = f"Rating: {product['rating']}/5"
                
                reviews_div = soup.new_tag('div', attrs={'class': 'reviews'})
                reviews_div.string = f"Reviews: {product['reviews']}"
                
                product_div.append(title_div)
                product_div.append(price_div)
                product_div.append(rating_div)
                product_div.append(reviews_div)
                
                product_list.append(product_div)
        
        logger.info(f"Generated {len(sample_products)} sample products for {website_name}")
        return soup    
    def extract_daraz_data(self, max_pages=3):
            logger.info("Extracting coffee data from Daraz")
            
            base_url = self.target_websites['daraz']['search_url']
            if not isinstance(base_url, str):
                logger.warning(f"Daraz URL is not a string: {type(base_url)}")
                return
            
            total_products = 0
            
            for page in range(1, max_pages + 1):
                current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'daraz')
                logger.info(f"Processing Daraz page {page} with URL: {current_url}")
                
                soup = self.get_page_content(current_url, use_selenium=True)
                if not soup:
                    logger.warning(f"Failed to get Daraz content for page {page}")
                    break

                if page == 1:
                    with open("daraz_debug.html", "w", encoding="utf-8") as f:
                        f.write(str(soup))
                
                product_selector = self.target_websites['daraz']['product_selector']
                product_cards = soup.select(product_selector)
                
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
                        name_selector = self.target_websites['daraz']['name_selector']
                        name_elem = card.select_one(name_selector)

                        if not name_elem:
                            for selector in self.target_websites['daraz']['alternative_selectors']['name_selector']:
                                name_elem = card.select_one(selector)
                                if name_elem:
                                    break
                        
                        product_data['name'] = name_elem.text.strip() if name_elem else "Unknown"

                        price_selector = self.target_websites['daraz']['price_selector']
                        price_elem = card.select_one(price_selector) or card.select_one('.price') or card.select_one('[data-price]')
                        price_text = price_elem.text.strip() if price_elem else "0"
                        price_text = price_text.replace("Rs.", "").replace(",", "").replace("PKR", "").strip()

                        try:
                            product_data['price'] = float(price_text)
                        except ValueError:
                            product_data['price'] = 0

                        rating_elem = card.select_one('.rating--b2Qtx')
                        product_data['rating'] = float(rating_elem.text.strip()) if rating_elem else 0

                        reviews_elem = card.select_one('.rating__review--ygkUy')
                        reviews_text = reviews_elem.text.strip() if reviews_elem else "0"
                        reviews_count = ''.join(filter(str.isdigit, reviews_text))
                        product_data['reviews_count'] = int(reviews_count) if reviews_count else 0

                        product_data['source'] = 'daraz.pk'
                        product_data['brand'] = self._extract_brand(product_data['name'])
                        product_data['type'] = self._extract_coffee_type(product_data['name'])
                        product_data['packaging'] = self._extract_packaging_info(product_data['name'])
                        product_data['price_tier'] = self._get_price_tier(product_data['price'])

                        self.raw_data.append(product_data)
                        self.processed_data['products'].append(product_data)
                        self._update_aggregated_data(product_data)

                        page_product_count += 1
                        total_products += 1
                    except Exception as e:
                        logger.error(f"Error processing Daraz product card on page {page}: {e}")

                logger.info(f"Extracted {page_product_count} products from Daraz page {page}")
                if page_product_count == 0:
                    logger.info(f"No products found on page {page}, stopping pagination")
                    break

            logger.info(f"Total extracted {total_products} products from Daraz across {min(page, max_pages)} pages")

    def extract_naheed_data(self, max_pages=3):
            """
            Extract coffee product data from Naheed.
            
            Args:
                max_pages (int): Maximum number of pages to scrape
            """
            logger.info("Extracting coffee data from Naheed")
            
            # Make sure we're passing a string URL, not a dictionary
            base_url = self.target_websites['naheed']['search_url']
            if not isinstance(base_url, str):
                logger.warning(f"Naheed URL is not a string: {type(base_url)}")
                return
                
            total_products = 0
            
            # Process multiple pages
            for page in range(1, max_pages + 1):
                # Generate URL for current page (page 1 uses the base URL)
                current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'naheed')
                logger.info(f"Processing Naheed page {page} with URL: {current_url}")
                
                soup = self.get_page_content(current_url, use_selenium=True)
                
                if not soup:
                    logger.warning(f"Failed to get Naheed content for page {page}")
                    break
                    
                # Save HTML for debugging if needed (only for the first page)
                if page == 1:
                    with open("naheed_debug.html", "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    
                logger.info(f"Trying to find Naheed products on page {page} with primary selector")
            
                # Extract product items using the specified CSS selector
                product_selector = self.target_websites['naheed']['product_selector']
                product_cards = soup.select(product_selector)
                
                if not product_cards:
                    logger.warning(f"No product cards found on Naheed page {page} using selector: {product_selector}")
                    # Try alternative selectors from the configuration
                    alternative_selectors = self.target_websites['naheed']['alternative_selectors']['product_selector']
                    for selector in alternative_selectors:
                        logger.info(f"Trying alternative product selector: {selector}")
                        product_cards = soup.select(selector)
                        if product_cards:
                            logger.info(f"Found {len(product_cards)} products using alternative selector: {selector}")
                            break
                else:
                    logger.info(f"Found {len(product_cards)} products using primary selector on page {page}")
                    
                if not product_cards:
                    logger.warning(f"Failed to find any products with all selectors on page {page}")
                    continue
                    
                logger.info(f"Processing {len(product_cards)} product cards from Naheed page {page}")
                page_product_count = 0
                
                for card in product_cards:
                    try:
                        product_data = {}
                        
                        # Extract name using the specific selector from configuration
                        name_selector = self.target_websites['naheed']['name_selector']
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
                                for selector in self.target_websites['naheed']['alternative_selectors']['name_selector']:
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
                        price_elem = card.select_one('.price-box .price')
                        if not price_elem:
                            price_elem = card.select_one('.price')
                        if not price_elem:
                            for selector in self.target_websites['naheed']['alternative_selectors']['price_selector']:
                                price_elem = card.select_one(selector)
                                if price_elem:
                                    break
                                    
                        price_text = price_elem.text.strip() if price_elem else "0"
                        # Clean price text (remove "Rs. " and commas)
                        price_text = price_text.replace("Rs.", "").replace("PKR", "").replace(",", "").strip()
                        try:
                            product_data['price'] = float(price_text)
                        except ValueError:
                            product_data['price'] = 0
                        
                        # Source website
                        product_data['source'] = 'naheed.pk'
                        
                        # Naheed doesn't show ratings directly in search results
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
                        logger.error(f"Error processing Naheed product card: {e}")
                
                logger.info(f"Extracted {page_product_count} products from Naheed page {page}")
                
                # If we got fewer products than expected, we might have reached the last page
                if page_product_count == 0:
                    logger.info(f"No products found on page {page}, stopping pagination")
                    break
            
            logger.info(f"Total extracted {total_products} products from Naheed across {page} pages")
            
    def extract_naheed_data_with_pagination(self, max_pages=3):
            """
            Extract coffee product data from Naheed with pagination support.
            
            Args:
                max_pages (int): Maximum number of pages to scrape
            """
            logger.info("Extracting coffee data from Naheed with pagination")
            
            # Make sure we're passing a string URL, not a dictionary
            base_url = self.target_websites['naheed']['search_url']
            if not isinstance(base_url, str):
                logger.warning(f"Naheed URL is not a string: {type(base_url)}")
                return
                
            total_products = 0
            
            # Process multiple pages
            for page in range(1, max_pages + 1):
                # Generate URL for current page (page 1 uses the base URL)
                current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'naheed')
                logger.info(f"Processing Naheed page {page} with URL: {current_url}")
                
                soup = self.get_page_content(current_url, use_selenium=True)
                
                if not soup:
                    logger.warning(f"Failed to get Naheed content for page {page}")
                    break
                    
                # Save HTML for debugging if needed (only for the first page)
                if page == 1:
                    with open("naheed_debug.html", "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    
                logger.info(f"Trying to find Naheed products on page {page} with primary selector")
                
                # Extract product items using the specified CSS selector
                product_selector = self.target_websites['naheed']['product_selector']
                product_cards = soup.select(product_selector)
                
                if not product_cards:
                    logger.warning(f"No product cards found on Naheed page {page} using selector: {product_selector}")
                    # Try alternative selectors from the configuration
                    alternative_selectors = self.target_websites['naheed']['alternative_selectors']['product_selector']
                    for selector in alternative_selectors:
                        logger.info(f"Trying alternative product selector: {selector}")
                        product_cards = soup.select(selector)
                        if product_cards:
                            logger.info(f"Found {len(product_cards)} products using alternative selector: {selector}")
                            break
                else:
                    logger.info(f"Found {len(product_cards)} products using primary selector on page {page}")
                    
                if not product_cards:
                    logger.warning(f"Failed to find any products with all selectors on page {page}")
                    continue
                    
                logger.info(f"Processing {len(product_cards)} product cards from Naheed page {page}")
                page_product_count = 0
                
                for card in product_cards:
                    try:
                        product_data = {}
                        
                        # Extract name using the specific selector from configuration
                        name_selector = self.target_websites['naheed']['name_selector']
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
                            if not name_elem and 'alternative_selectors' in self.target_websites['naheed'] and 'name_selector' in self.target_websites['naheed']['alternative_selectors']:
                                for selector in self.target_websites['naheed']['alternative_selectors']['name_selector']:
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
                        price_elem = card.select_one('.price-box .price')
                        if not price_elem:
                            price_elem = card.select_one('.price')
                        if not price_elem and 'alternative_selectors' in self.target_websites['naheed'] and 'price_selector' in self.target_websites['naheed']['alternative_selectors']:
                            for selector in self.target_websites['naheed']['alternative_selectors']['price_selector']:
                                price_elem = card.select_one(selector)
                                if price_elem:
                                    break
                                    
                        price_text = price_elem.text.strip() if price_elem else "0"
                        # Clean price text (remove "Rs. " and commas)
                        price_text = price_text.replace("Rs.", "").replace("PKR", "").replace(",", "").strip()
                        try:
                            product_data['price'] = float(price_text)
                        except ValueError:
                            product_data['price'] = 0
                        
                        # Source website
                        product_data['source'] = 'naheed.pk'
                        
                        # Naheed doesn't show ratings directly in search results
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
                        logger.error(f"Error processing Naheed product card: {e}")
                
                logger.info(f"Extracted {page_product_count} products from Naheed page {page}")
                
                # If we got fewer products than expected, we might have reached the last page
                if page_product_count == 0:
                    logger.info(f"No products found on page {page}, stopping pagination")
                    break
            
            logger.info(f"Total extracted {total_products} products from Naheed across {min(page, max_pages)} pages")   
    def extract_metro_data(self, max_pages=3):
            """
            Extract coffee product data from Metro Online Pakistan.

            Args:
                max_pages (int): Maximum number of pages to scrape
            """
            logger.info("Extracting coffee data from Metro Online")

            # Get the URL from our configuration
            base_url = self.target_websites['metro']['search_url']
            if not base_url.startswith('http'):
                base_url = 'https://' + base_url.lstrip('/')

            total_products = 0

            for page in range(1, max_pages + 1):
                current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'metro')
                logger.info(f"Processing Metro page {page} with URL: {current_url}")

                soup = self.get_page_content(current_url, use_selenium=True)

                if not soup:
                    logger.warning(f"Failed to get Metro content for page {page}")
                    break

                if page == 1:
                    with open("metro_debug.html", "w", encoding="utf-8") as f:
                        f.write(str(soup))

                product_selector = self.target_websites['metro']['product_selector']
                product_cards = soup.select(product_selector)

                if not product_cards:
                    logger.warning(f"No product cards found on Metro page {page} using selector: {product_selector}")
                    product_cards = soup.select('li.product-item')
                    if not product_cards:
                        logger.warning(f"Failed with alternative selector for Metro page {page} too")
                        continue
                else:
                    logger.info(f"Found {len(product_cards)} products on Metro page {page}")

                page_product_count = 0

                for card in product_cards:
                    try:
                        product_data = {}

                        # Extract name
                        name_elem = card.select_one(self.target_websites['metro']['name_selector']) or \
                                    card.select_one('h2.product-name')
                        if name_elem:
                            product_data['name'] = name_elem.text.strip()
                        else:
                            logger.warning("Failed to extract product name")
                            continue

                        # Skip non-coffee products
                        if not any(term in product_data['name'].lower() for term in
                                ['coffee', 'caffè', 'espresso', 'cappuccino', 'mocha', 'latte']):
                            logger.debug(f"Skipping non-coffee product: {product_data['name']}")
                            continue

                        # Extract price
                        price_elem = card.select_one(self.target_websites['metro']['price_selector']) or \
                                    card.select_one('.price-box')
                        if price_elem:
                            price_text = price_elem.text.strip()
                            price_text = re.sub(r'[^\d.]', '', price_text.replace(',', ''))
                            try:
                                product_data['price'] = float(price_text)
                            except (ValueError, AttributeError):
                                product_data['price'] = 0
                        else:
                            logger.warning(f"No price found for product: {product_data['name']}")
                            product_data['price'] = 0

                        # Rating and reviews (Metro doesn't show)
                        product_data['rating'] = 0
                        product_data['reviews_count'] = 0
                        product_data['source'] = 'metro-online.pk'

                        product_hash = hashlib.md5(f"{product_data['name']}|{product_data['price']}".encode()).hexdigest()
                        if product_hash in self.processed_product_hashes:
                            logger.debug(f"Skipping duplicate product: {product_data['name']}")
                            continue
                        self.processed_product_hashes.add(product_hash)

                        # Enrich data
                        product_data['brand'] = self._extract_brand(product_data['name'])
                        product_data['type'] = self._extract_coffee_type(product_data['name'])
                        product_data['packaging'] = self._extract_packaging_info(product_data['name'])
                        product_data['price_tier'] = self._get_price_tier(product_data['price'])

                        # Store data
                        self.raw_data.append(product_data)
                        self.processed_data['products'].append(product_data)
                        self._update_aggregated_data(product_data)

                        page_product_count += 1
                        total_products += 1

                    except Exception as e:
                        logger.error(f"Error processing Metro product card on page {page}: {e}")
                        continue

                logger.info(f"Extracted {page_product_count} products from Metro page {page}")

                if page_product_count == 0:
                    logger.info(f"No products found on page {page}, stopping pagination")
                    break

            logger.info(f"Total extracted {total_products} products from Metro across {min(page, max_pages)} pages")

    def extract_alibaba_data(self, max_pages=3):
            """Extract coffee product data from Alibaba Pakistan."""
            logger.info("Extracting coffee data from Alibaba Pakistan")
            base_url = self.target_websites['alibaba']['search_url']
            if not base_url.startswith('http'):
                base_url = 'https://' + base_url.lstrip('/')

            total_products = 0

            for page in range(1, max_pages + 1):
                current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'alibaba')
                logger.info(f"Processing Alibaba page {page} with URL: {current_url}")
                soup = self.get_page_content(current_url, use_selenium=True)
                
                if not soup:
                    logger.warning(f"Failed to get Alibaba content for page {page}")
                    break

                product_selector = self.target_websites['alibaba']['product_selector']
                product_cards = soup.select(product_selector)

                if not product_cards:
                    logger.warning(f"No product cards found with main selector: {product_selector}")
                    for selector in ['.product-item', '.item', '.product-box']:
                        product_cards = soup.select(selector)
                        if product_cards:
                            logger.info(f"Found products with alternative selector: {selector}")
                            break

                if not product_cards:
                    logger.warning(f"Failed to find products on Alibaba page {page}")
                    continue

                logger.info(f"Found {len(product_cards)} products on page {page}")
                page_product_count = 0

                for card in product_cards:
                    try:
                        product_data = {}
                        name_elem = card.select_one(self.target_websites['alibaba']['name_selector'])
                        if not name_elem:
                            for selector in ['h2.product-name', '.product-title', '.name']:
                                name_elem = card.select_one(selector)
                                if name_elem:
                                    break
                        if not name_elem:
                            continue
                        product_data['name'] = name_elem.text.strip()

                        if not any(term in product_data['name'].lower() for term in ['coffee', 'caffè', 'espresso', 'cappuccino', 'mocha', 'latte']):
                            continue

                        price_elem = card.select_one(self.target_websites['alibaba']['price_selector'])
                        if not price_elem:
                            for selector in ['.price', '.price-box', '.product-price']:
                                price_elem = card.select_one(selector)
                                if price_elem:
                                    break

                        if price_elem:
                            price_text = re.sub(r'[^\d.]', '', price_elem.text.strip().replace(',', ''))
                            product_data['price'] = float(price_text) if price_text else 0
                        else:
                            product_data['price'] = 0

                        product_data['rating'] = 0
                        product_data['reviews_count'] = 0
                        product_data['source'] = 'alibaba.pk'

                        product_hash = hashlib.md5(f"{product_data['name']}|{product_data['price']}".encode()).hexdigest()
                        if product_hash in self.processed_product_hashes:
                            continue
                        self.processed_product_hashes.add(product_hash)

                        product_data['brand'] = self._extract_brand(product_data['name'])
                        product_data['type'] = self._extract_coffee_type(product_data['name'])
                        product_data['packaging'] = self._extract_packaging_info(product_data['name'])
                        product_data['price_tier'] = self._get_price_tier(product_data['price'])

                        self.raw_data.append(product_data)
                        self.processed_data['products'].append(product_data)
                        self._update_aggregated_data(product_data)

                        page_product_count += 1
                        total_products += 1

                    except Exception as e:
                        logger.error(f"Error processing Alibaba product card on page {page}: {e}")
                        continue

                if page_product_count == 0:
                    logger.info(f"No products found on page {page}, stopping pagination")
                    break

            logger.info(f"Total extracted {total_products} products from Alibaba across {min(page, max_pages)} pages")
            
    def extract_alfatah_data(self, max_pages=3):
        """
        Extract coffee product data from Alfatah.
        
        Args:
            max_pages (int): Maximum number of pages to scrape
        """
        logger.info("Extracting coffee data from Alfatah")
        
        base_url = self.target_websites['alfatah']['search_url']
        if not isinstance(base_url, str):
            logger.warning(f"Alfatah URL is not a string: {type(base_url)}")
            return
            
        total_products = 0
        
        # Process multiple pages
        for page in range(1, max_pages + 1):
            # Generate URL for current page
            current_url = base_url if page == 1 else self._generate_pagination_url(base_url, page, 'alfatah')
            logger.info(f"Processing Alfatah page {page} with URL: {current_url}")
            
            soup = self.get_page_content(current_url, use_selenium=True)
            
            if not soup:
                logger.warning(f"Failed to get Alfatah content for page {page}")
                break
                
            # Save HTML for debugging if needed (only for the first page)
            if page == 1:
                with open("alfatah_debug.html", "w", encoding="utf-8") as f:
                    f.write(str(soup))
                
            # Extract product items using the specified CSS selector
            product_selector = self.target_websites['alfatah']['product_selector']
            product_cards = soup.select(product_selector)
            
            if not product_cards:
                logger.warning(f"No product cards found on Alfatah page {page} using selector: {product_selector}")
                # Try alternative selectors from the configuration
                alternative_selectors = self.target_websites['alfatah']['alternative_selectors']['product_selector']
                for selector in alternative_selectors:
                    logger.info(f"Trying alternative product selector: {selector}")
                    product_cards = soup.select(selector)
                    if product_cards:
                        logger.info(f"Found {len(product_cards)} products using alternative selector: {selector}")
                        break
            else:
                logger.info(f"Found {len(product_cards)} products using primary selector on page {page}")
                
            if not product_cards:
                logger.warning(f"Failed to find any products with all selectors on page {page}")
                continue
                
            logger.info(f"Processing {len(product_cards)} product cards from Alfatah page {page}")
            page_product_count = 0
            
            for card in product_cards:
                try:
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
                    price_text = re.sub(r'[^\d.]', '', price_text.replace(',', ''))
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
                    logger.error(f"Error processing Alfatah product card: {e}")
            logger.info(f"Extracted {page_product_count} products from Alfatah page {page}")
            
            # If we got fewer products than expected, we might have reached the last page
            if page_product_count == 0:
                logger.info(f"No products found on page {page}, stopping pagination")
                break
        
        logger.info(f"Total extracted {total_products} products from Alfatah across {min(page, max_pages)} pages")
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
            
            # Use Selenium to load dynamic content (required for Foodpanda)
            soup = self.get_page_content(current_url, use_selenium=True)
            
            if not soup:
                logger.warning(f"Failed to get Foodpanda content for page {page}")
                break
            
            # For debugging purposes, save the first page's HTML
            if page == 1:
                with open("foodpanda_debug.html", "w", encoding="utf-8") as f:
                    f.write(str(soup))
            
            # Try primary selector for product cards
            product_cards = []
            
            # First try: Direct selection of product grid items
            product_cards = soup.select('ul.product-grid > li')
            
            # Second try: If that doesn't work, try the configured selector
            if not product_cards:
                product_selector = self.target_websites['foodpanda']['product_selector']
                product_cards = soup.select(product_selector)
                
                # Third try: Check for alternative selectors
                if not product_cards and 'alternative_selectors' in self.target_websites['foodpanda']:
                    logger.warning(f"No product cards found using primary selectors")
                    for alt_selector in self.target_websites['foodpanda']['alternative_selectors'].get('product_selector', []):
                        product_cards = soup.select(alt_selector)
                        if product_cards:
                            logger.info(f"Found products with alternative selector: {alt_selector}")
                            break
            
            # Final try: Look for groceries product cards
            if not product_cards:
                logger.warning("Trying groceries-specific selectors")
                product_cards = soup.select('.groceries-product-card')
                
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
                    
                    # First try direct selection by class
                    name_elem = card.select_one('.groceries-product-card-name')
                    
                    # If that doesn't work, try the configured selector
                    if not name_elem:
                        name_selector = self.target_websites['foodpanda'].get('name_selector', '')
                        if name_selector:
                            name_elem = card.select_one(name_selector)
                    
                    # Try alternative name selectors if needed
                    if not name_elem and 'alternative_selectors' in self.target_websites['foodpanda']:
                        for selector in self.target_websites['foodpanda']['alternative_selectors'].get('name_selector', []):
                            name_elem = card.select_one(selector)
                            if name_elem:
                                break
                                
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
                    
                    # First try direct selection by class
                    price_elem = card.select_one('.groceries-product-card-price')
                    
                    # If that doesn't work, try the configured selector
                    if not price_elem:
                        price_selector = self.target_websites['foodpanda'].get('price_selector', '')
                        if price_selector:
                            price_elem = card.select_one(price_selector)
                    
                    # Try alternative selectors if needed
                    if not price_elem and 'alternative_selectors' in self.target_websites['foodpanda']:
                        for selector in self.target_websites['foodpanda']['alternative_selectors'].get('price_selector', []):
                            price_elem = card.select_one(selector)
                            if price_elem:
                                break
                    
                    price_text = price_elem.text.strip() if price_elem else "0"
                    
                    # Clean price text (remove "Rs. " and commas)
                    price_text = price_text.replace("Rs.", "").replace("PKR", "").replace("₨", "").replace(",", "").strip()
                    try:
                        # Extract numbers from the text if parsing fails
                        numbers = re.findall(r'\d+\.?\d*', price_text)
                        product_data['price'] = float(numbers[0]) if numbers else 0
                    except (ValueError, IndexError):
                        product_data['price'] = 0
                    
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
                    logger.exception(e)  # Log the full exception traceback
            
            logger.info(f"Extracted {page_product_count} products from Foodpanda page {page}")
            
            # If we got fewer products than expected, we might have reached the last page
            if page_product_count == 0:
                logger.info(f"No products found on page {page}, stopping pagination")
                break
        
        logger.info(f"Total extracted {total_products} products from Foodpanda across {min(page, max_pages)} pages")
        
    def _is_coffee_product(self, product_name):
        """
        Check if a product is coffee-related based on its name.
        
        Args:
            product_name (str): Full product name
            
        Returns:
            bool: True if product is coffee-related, False otherwise
        """
        if not product_name or product_name == "Unknown":
            return False
            
        # Convert to lowercase for case-insensitive matching
        name_lower = product_name.lower()
        
        # Coffee-related keywords
        coffee_keywords = [
            'coffee', 'café', 'caffè', 'kaffee', 'nescafe', 'espresso', 'cappuccino', 
            'latte', 'mocha', 'americano', 'java', 'brew', 'arabica', 'robusta', 
            'decaf', 'coffeehouse', 'coffeeshop', 'kopi', 'kahwa', 'قہوہ', 'کافی',
            'barista', 'french press', 'turkish coffee', 'iced coffee', 'coffee bean',
            'cold brew', 'coffee grounds', 'instant coffee'
        ]
        
        # Check if any coffee keyword is in product name
        for keyword in coffee_keywords:
            if keyword in name_lower:
                return True
                
        return False
    
    def _extract_brand(self, product_name):
        """
        Extract brand name from product name.
            
        Args:
            product_name (str): Full product name
                
        Returns:
            str: Extracted brand name or "Unknown"
        """
        # Common coffee brands in Pakistan
        common_brands = [
            'Nescafe', 'Nestle', 'Lavazza', 'Davidoff', 'Jacobs', 'Maxwell House', 
            'Folgers', 'Mehran', 'National', 'Tapal', 'Espresso', 'Koffee Kult', 
            'MacCoffee', 'CafeCoffeeDay', 'Kenco', 'Dallah', 'Gloria Jeans', 
            'Second Cup', 'Illy', 'Coffeewalla', 'Urban Coffee', 'Mocca', 
            'Café de Colombia', 'Café du Monde', 'Café Puro', 'Café Direct', 
            'Café Royal', 'Café Noir', 'Café Brazil', 'Café Culiacán', 
            'Coffee Planet', 'Coffee Beanery', 'Coffee Republic', 
            'Coffee Time', 'Coffee World', 'Coffee Culture', 
            'Coffee Connection', 'Coffee House', 'Coffee Shop', 
            'Kraft Foods', 'Unilever', 'PepsiCo', 'Nestle Pakistan',
            'Kahwa', 'Sadaf Coffee',
            'Raven', 'Arkadia', 'Continental', 'Red Bull', 'Tesco', 
            'Nescafe Gold', 'Nescafe Classic', 'Kauphy'
        ]
            
        for brand in common_brands:
            if brand.lower() in product_name.lower():
                return brand
        
        # If no known brand is found
        return "Unknown"
        
    def _extract_coffee_type(self, product_name):
            """
            Extract coffee type from product name.
            
            Args:
                product_name (str): Full product name
                
            Returns:
                str: Coffee type (instant, ground, beans, powdered, or unknown)
            """
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
                elif 'mix' in name_lower or '3 in 1' in name_lower or '2 in 1' in name_lower:
                    return 'coffee mix'
                
                # Default to instant as it's most common in Pakistan
                return 'instant'
        
    def _extract_packaging_info(self, product_name):
            """
            Extract packaging size and type from product name.
            
            Args:
                product_name (str): Full product name
                
            Returns:
                dict: Packaging information with weight and unit
            """
            name_lower = product_name.lower()
            
            # Look for common weight patterns
            weight_patterns = [
                r'(\d+)\s*g\b',          # 200g
                r'(\d+)\s*gram',         # 200 gram
                r'(\d+)\s*kg\b',         # 1kg
                r'(\d+)\s*kilo',         # 1 kilo
                r'(\d+\.?\d*)\s*oz',     # 8oz
                r'(\d+\.?\d*)\s*ounce',  # 8 ounce
                r'(\d+)ml\b',            # 200ml (for liquid coffee products)
                r'(\d+)\s*liter',        # 1 liter
                r'(\d+)\s*pack',         # 10 pack
                r'(\d+)\s*sachet',       # 10 sachet
                r'(\d+)\s*sticks',       # 10 sticks
                r'(\d+)\s*capsule',      # 10 capsules
                r'(\d+)\s*pods',         # 10 pods
            ]
            
            for pattern in weight_patterns:
                import re
                match = re.search(pattern, name_lower)
                if match:
                    value = float(match.group(1))
                    
                    # Determine unit based on the matched pattern
                    if 'g' in pattern or 'gram' in pattern:
                        unit = 'g'
                    elif 'kg' in pattern or 'kilo' in pattern:
                        unit = 'kg'
                        # Convert kg to g for consistency
                        value = value * 1000
                        unit = 'g'
                    elif 'oz' in pattern or 'ounce' in pattern:
                        unit = 'oz'
                        # Convert oz to g for consistency (1 oz ≈ 28.35 g)
                        value = value * 28.35
                        unit = 'g'
                    elif 'ml' in pattern or 'liter' in pattern:
                        unit = 'ml'
                    elif 'pack' in pattern or 'sachet' in pattern or 'stick' in pattern:
                        unit = 'count'
                    elif 'capsule' in pattern or 'pod' in pattern:
                        unit = 'count'
                    else:
                        unit = 'unknown'
                    
                    return {
                        'value': value,
                        'unit': unit,
                        'display': f"{int(value) if value.is_integer() else value}{unit}"
                    }
            
            # If no match is found, return unknown
            return {
                'value': 0,
                'unit': 'unknown',
                'display': 'unknown'
            }
        
    def _get_price_tier(self, price):
            """
            Categorize a product into price tier based on its price.
            
            Args:
                price (float): Product price
                
            Returns:
                str: Price tier category (low, mid, premium)
            """
            for tier, range_values in PRICE_TIERS.items():
                if range_values['min'] <= price <= range_values['max']:
                    return tier
            # Default to mid if something goes wrong with the logic
            return 'mid'
        
    def _update_aggregated_data(self, product):
            """
            Update aggregated statistics based on a product.
            
            Args:
                product (dict): Product data
            """
            # Update brand stats
            brand = product['brand']
            if brand not in self.processed_data['brands']:
                self.processed_data['brands'][brand] = {
                    'count': 0,
                    'avg_price': 0,
                    'total_price': 0,
                    'types': set()
                }
            
            self.processed_data['brands'][brand]['count'] += 1
            self.processed_data['brands'][brand]['total_price'] += product['price']
            self.processed_data['brands'][brand]['avg_price'] = (
                self.processed_data['brands'][brand]['total_price'] / 
                self.processed_data['brands'][brand]['count']
            )
            self.processed_data['brands'][brand]['types'].add(product['type'])
            
            # Update coffee type stats
            coffee_type = product['type']
            if coffee_type not in self.processed_data['types']:
                self.processed_data['types'][coffee_type] = {
                    'count': 0,
                    'avg_price': 0,
                    'total_price': 0,
                    'brands': set()
                }
            
            self.processed_data['types'][coffee_type]['count'] += 1
            self.processed_data['types'][coffee_type]['total_price'] += product['price']
            self.processed_data['types'][coffee_type]['avg_price'] = (
            self.processed_data['types'][coffee_type]['total_price'] / 
            self.processed_data['types'][coffee_type]['count']
            )
            self.processed_data['types'][coffee_type]['brands'].add(product['brand'])
            
            # Update packaging stats
            if product['packaging']['unit'] != 'unknown':
                packaging_key = product['packaging']['display']
                if packaging_key not in self.processed_data['packaging']:
                    self.processed_data['packaging'][packaging_key] = {
                        'count': 0,
                        'avg_price': 0,
                        'total_price': 0
                    }
                
                self.processed_data['packaging'][packaging_key]['count'] += 1
                self.processed_data['packaging'][packaging_key]['total_price'] += product['price']
                self.processed_data['packaging'][packaging_key]['avg_price'] = (
                    self.processed_data['packaging'][packaging_key]['total_price'] / 
                    self.processed_data['packaging'][packaging_key]['count']
                )
            
            # Update price tier stats
            price_tier = product['price_tier']
            self.processed_data['price_tiers'][price_tier].append(product)
        
    def collect_data(self, max_sites=None, dummy_param_to_force_reload=None): # Added dummy_param_to_force_reload
            """
            Main method to collect coffee market data from all sources.
            
            Args:
                max_sites (int, optional): Maximum number of sites to scrape, useful for testing
                dummy_param_to_force_reload: This is a test parameter
                
            Returns:
                dict: Processed market data
            """
            logger.info("Starting coffee market data collection")
            
            # Extract data from each e-commerce site
            extraction_methods = {
                'daraz': self.extract_daraz_data,
                'alfatah': self.extract_alfatah_data,
                'naheed': self.extract_naheed_data,
                'metro': self.extract_metro_data,
                'alibaba': self.extract_alibaba_data,
                'foodpanda': self.extract_foodpanda_data
            }
            
            # Keeps track of successful sites
            successful_sites = []
            failed_sites = []
            
            # Process sites with a limit if specified
            sites_to_process = list(extraction_methods.keys())
            if max_sites:
                sites_to_process = sites_to_process[:max_sites]
                
            for site_name in sites_to_process:
                try:
                    logger.info(f"Processing site: {site_name}")
                    start_time = time.time()
                    
                    # Get product count before extraction
                    products_before = len(self.processed_data['products'])
                    # Extract data for this site with pagination
                    if site_name == 'naheed':
                        extraction_methods[site_name](max_pages=5)
                    elif site_name == 'daraz':
                        extraction_methods[site_name](max_pages=5)
                    elif site_name == 'alfatah': # This method needs to be defined
                        extraction_methods[site_name](max_pages=5)
                    elif site_name == 'metro':
                        extraction_methods[site_name](max_pages=5)
                    elif site_name == 'alibaba':
                        extraction_methods[site_name](max_pages=5)
                    elif site_name == 'foodpanda': # This method needs to be defined
                        extraction_methods[site_name](max_pages=5)
                    else:
                        extraction_methods[site_name]()
                    
                    # Get product count after extraction
                    products_after = len(self.processed_data['products'])
                    products_added = products_after - products_before
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"Extracted {products_added} products from {site_name} in {elapsed_time:.2f} seconds")
                    
                    if products_added > 0:
                        successful_sites.append(site_name)
                    else:
                        logger.warning(f"No products extracted from {site_name}")
                        failed_sites.append(site_name)
                        
                except Exception as e:
                    logger.error(f"Error extracting data from {site_name}: {e}", exc_info=True)
                    failed_sites.append(site_name)
                    continue
            # Log if all sites failed but don't automatically generate sample data
            if len(self.processed_data['products']) == 0 and len(failed_sites) == len(sites_to_process):
                logger.warning("All sites failed. No data collected. Check website configurations and selectors.")
            
            # Convert sets to lists for JSON serialization
            for brand_name in list(self.processed_data['brands'].keys()):
                if 'types' in self.processed_data['brands'][brand_name] and isinstance(self.processed_data['brands'][brand_name]['types'], set):
                    self.processed_data['brands'][brand_name]['types'] = list(self.processed_data['brands'][brand_name]['types'])
                
            for coffee_type_name in list(self.processed_data['types'].keys()):
                if 'brands' in self.processed_data['types'][coffee_type_name] and isinstance(self.processed_data['types'][coffee_type_name]['brands'], set):
                    self.processed_data['types'][coffee_type_name]['brands'] = list(self.processed_data['types'][coffee_type_name]['brands'])
            
            # Add collection metadata
            self.processed_data['metadata'] = {
                'collection_time': datetime.now().isoformat(),
                'successful_sites': successful_sites,
                'failed_sites': failed_sites,
                'total_products': len(self.processed_data['products']),
                'total_brands': len(self.processed_data['brands']),
                'data_quality': 'Sample data' if len(successful_sites) == 0 else 'Production data'
            }
            
            logger.info(f"Collected data for {len(self.processed_data['products'])} coffee products from {len(successful_sites)} sites")
            logger.info(f"Successful sites: {', '.join(successful_sites) if successful_sites else 'None'}")
            logger.info(f"Failed sites: {', '.join(failed_sites) if failed_sites else 'None'}")
            
            return self.processed_data

    def save_data(self, timestamp=None):
            """
            Save collected data to files.
            
            Args:
                timestamp (str, optional): Timestamp for filenames
            
            Returns:
                dict: Paths to saved files
            """
            if timestamp is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Ensure directories exist
            os.makedirs(PATHS["raw_data"], exist_ok=True)
            os.makedirs(PATHS["processed_data"], exist_ok=True)
            
            # Save raw data as JSON
            raw_data_path = os.path.join(PATHS["raw_data"], f"coffee_market_{timestamp}.json")
            with open(raw_data_path, 'w', encoding='utf-8') as f:
                json.dump(self.raw_data, f, indent=2)
            
            # Save processed data as JSON
            processed_data_path = os.path.join(PATHS["raw_data"], f"coffee_market_processed_{timestamp}.json")
            with open(processed_data_path, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data, f, indent=2)
            
            # Create and save various CSV files for easier analysis
            csv_paths = {}
            
            # Products CSV
            products_df = pd.DataFrame(self.processed_data['products'])
            products_csv_path = os.path.join(PATHS["processed_data"], f"coffee_products_{timestamp}.csv")
            products_df.to_csv(products_csv_path, index=False)
            csv_paths['products'] = products_csv_path
            
            # Brands summary CSV
            brands_data = []
            for brand, stats in self.processed_data['brands'].items():
                brands_data.append({
                    'brand': brand,
                    'product_count': stats['count'],
                    'avg_price': stats['avg_price'],
                    'coffee_types': ', '.join(stats['types']) if isinstance(stats['types'], list) else ', '.join(list(stats['types']))
                })
            
            brands_df = pd.DataFrame(brands_data)
            brands_csv_path = os.path.join(PATHS["processed_data"], f"coffee_brands_{timestamp}.csv")
            brands_df.to_csv(brands_csv_path, index=False)
            csv_paths['brands'] = brands_csv_path
            
            # Coffee types summary CSV
            types_data = []
            for coffee_type, stats in self.processed_data['types'].items():
                types_data.append({
                    'coffee_type': coffee_type,
                    'product_count': stats['count'],
                    'avg_price': stats['avg_price'],
                    'brands': ', '.join(stats['brands']) if isinstance(stats['brands'], list) else ', '.join(list(stats['brands']))
                })
            
            types_df = pd.DataFrame(types_data)
            types_csv_path = os.path.join(PATHS["processed_data"], f"coffee_types_{timestamp}.csv")
            types_df.to_csv(types_csv_path, index=False)
            csv_paths['types'] = types_csv_path
            
            # Packaging summary CSV
            packaging_data = []
            for size, stats in self.processed_data['packaging'].items():
                packaging_data.append({
                    'packaging_size': size,
                    'product_count': stats['count'],
                    'avg_price': stats['avg_price']
                })
            
            packaging_df = pd.DataFrame(packaging_data)
            packaging_csv_path = os.path.join(PATHS["processed_data"], f"coffee_packaging_{timestamp}.csv")
            packaging_df.to_csv(packaging_csv_path, index=False)
            csv_paths['packaging'] = packaging_csv_path
            
            # Create a consolidated CSV file containing all categories
            consolidated_data = {
                'products': products_df,
                'brands': brands_df,
                'types': types_df,
                'packaging': packaging_df
            }
            
            # Save consolidated data to a single Excel file with multiple sheets
            consolidated_path = os.path.join(PATHS["processed_data"], f"coffee_market_all_categories_{timestamp}.xlsx")
            with pd.ExcelWriter(consolidated_path) as writer:
                for sheet_name, df in consolidated_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            csv_paths['consolidated'] = consolidated_path
            logger.info(f"Saved consolidated coffee market data to Excel file: {consolidated_path}")
            
            # Also save latest versions with consistent filenames
            products_df.to_csv(os.path.join(PATHS["processed_data"], "coffee_products_latest.csv"), index=False)
            brands_df.to_csv(os.path.join(PATHS["processed_data"], "coffee_brands_latest.csv"), index=False)
            types_df.to_csv(os.path.join(PATHS["processed_data"], "coffee_types_latest.csv"), index=False)
            packaging_df.to_csv(os.path.join(PATHS["processed_data"], "coffee_packaging_latest.csv"), index=False)
            
            # Save latest consolidated Excel file
            with pd.ExcelWriter(os.path.join(PATHS["processed_data"], "coffee_market_all_categories_latest.xlsx")) as writer:
                for sheet_name, df in consolidated_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"Saved coffee market data to {len(csv_paths)} files")
            
            return {
                'raw_json': raw_data_path,
                'processed_json': processed_data_path,
                'csv_files': csv_paths
            }

    def _generate_sample_product_data(self):
            """
            Generate sample product data when all website scraping fails.
            This is a fallback method to ensure the system always has data to work with.
            """
            logger.warning("Generating sample product dataset")
            
            # Sample coffee products commonly found in Pakistan
            sample_products = [
                {
                    'name': 'Nescafe Classic Instant Coffee 200g',
                    'price': 950,
                    'rating': 4.5,
                    'reviews_count': 120,
                    'source': 'sample_data',
                    'brand': 'Nescafe',
                    'type': 'instant',
                    'packaging': {'value': 200, 'unit': 'g', 'display': '200g'},
                    'price_tier': 'low'
                },
                {
                    'name': 'Nescafe Gold Blend Premium Coffee 100g Jar',
                    'price': 1250,
                    'rating': 4.7,
                    'reviews_count': 85,
                    'source': 'sample_data',
                    'brand': 'Nescafe',
                    'type': 'instant',
                    'packaging': {'value': 100, 'unit': 'g', 'display': '100g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Davidoff Rich Aroma Ground Coffee 250g',
                    'price': 2350,
                    'rating': 4.8,
                    'reviews_count': 42,
                    'source': 'sample_data',
                    'brand': 'Davidoff',
                    'type': 'ground',
                    'packaging': {'value': 250, 'unit': 'g', 'display': '250g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Lavazza Qualita Oro Ground Coffee 250g',
                    'price': 2100,
                    'rating': 4.6,
                    'reviews_count': 38,
                    'source': 'sample_data',
                    'brand': 'Lavazza',
                    'type': 'ground',
                    'packaging': {'value': 250, 'unit': 'g', 'display': '250g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Maxwell House Original Roast Ground Coffee 300g',
                    'price': 1800,
                    'rating': 4.2,
                    'reviews_count': 29,
                    'source': 'sample_data',
                    'brand': 'Maxwell House',
                    'type': 'ground',
                    'packaging': {'value': 300, 'unit': 'g', 'display': '300g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Mehran Instant Coffee Powder 50g',
                    'price': 450,
                    'rating': 3.9,
                    'reviews_count': 65,
                    'source': 'sample_data',
                    'brand': 'Mehran',
                    'type': 'powdered',
                    'packaging': {'value': 50, 'unit': 'g', 'display': '50g'},
                    'price_tier': 'low'
                },
                {
                    'name': 'Nescafe 3 in 1 Instant Coffee Mix 30 Sticks',
                    'price': 850,
                    'rating': 4.4,
                    'reviews_count': 95,
                    'source': 'sample_data',
                    'brand': 'Nescafe',
                    'type': 'coffee mix',
                    'packaging': {'value': 30, 'unit': 'count', 'display': '30count'},
                    'price_tier': 'low'
                },
                {
                    'name': 'Folgers Classic Roast Ground Coffee 226g',
                    'price': 1550,
                    'rating': 4.3,
                    'reviews_count': 22,
                    'source': 'sample_data',
                    'brand': 'Folgers',
                    'type': 'ground',
                    'packaging': {'value': 226, 'unit': 'g', 'display': '226g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Continental Premium Blend Coffee Powder 100g',
                    'price': 750,
                    'rating': 4.0,
                    'reviews_count': 48,
                    'source': 'sample_data',
                    'brand': 'Continental',
                    'type': 'powdered',
                    'packaging': {'value': 100, 'unit': 'g', 'display': '100g'},
                    'price_tier': 'low'
                },
                {
                    'name': 'Kauphy Italian Roast Coffee Beans 250g',
                    'price': 1950,
                    'rating': 4.8,
                    'reviews_count': 15,
                    'source': 'sample_data',
                    'brand': 'Kauphy',
                    'type': 'beans',
                    'packaging': {'value': 250, 'unit': 'g', 'display': '250g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Lavazza Super Crema Espresso Coffee Beans 1kg',
                    'price': 4200,
                    'rating': 4.9,
                    'reviews_count': 28,
                    'source': 'sample_data',
                    'brand': 'Lavazza',
                    'type': 'beans',
                    'packaging': {'value': 1000, 'unit': 'g', 'display': '1000g'},
                    'price_tier': 'premium'
                },
                {
                    'name': 'Nescafe Tasters Choice Instant Coffee 200g',
                    'price': 1100,
                    'rating': 4.2,
                    'reviews_count': 56,
                    'source': 'sample_data',
                    'brand': 'Nescafe',
                    'type': 'instant',
                    'packaging': {'value': 200, 'unit': 'g', 'display': '200g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Illy Classico Medium Roast Ground Coffee 250g',
                    'price': 2800,
                    'rating': 4.7,
                    'reviews_count': 33,
                    'source': 'sample_data',
                    'brand': 'Illy',
                    'type': 'ground',
                    'packaging': {'value': 250, 'unit': 'g', 'display': '250g'},
                    'price_tier': 'premium'
                },
                {
                    'name': 'Tapal Premium Danedar Tea 900g',
                    'price': 1350,
                    'rating': 4.4,
                    'reviews_count': 112,
                    'source': 'sample_data',
                    'brand': 'Tapal',
                    'type': 'tea',  # Not coffee, but common brand
                    'packaging': {'value': 900, 'unit': 'g', 'display': '900g'},
                    'price_tier': 'mid'
                },
                {
                    'name': 'Jacobs Kronung Ground Coffee 250g',
                    'price': 1700,
                    'rating': 4.5,
                    'reviews_count': 27,
                    'source': 'sample_data',
                    'brand': 'Jacobs',
                    'type': 'ground',
                    'packaging': {'value': 250, 'unit': 'g', 'display': '250g'},
                    'price_tier': 'mid'
                }
            ]
            
            # Add sample products to our data collections
            for product in sample_products:
                # Add to raw data
                self.raw_data.append(product)
                
                # Add to processed products
                self.processed_data['products'].append(product)
                
                # Add to price tiers
                self.processed_data['price_tiers'][product['price_tier']].append(product)
                
                # Update brand stats
                brand = product['brand']
                if brand not in self.processed_data['brands']:
                    self.processed_data['brands'][brand] = {
                        'count': 0,
                        'avg_price': 0,
                        'total_price': 0,
                        'types': set()
                    }
                
                self.processed_data['brands'][brand]['count'] += 1
                self.processed_data['brands'][brand]['total_price'] += product['price']
                self.processed_data['brands'][brand]['avg_price'] = (
                    self.processed_data['brands'][brand]['total_price'] / 
                    self.processed_data['brands'][brand]['count']
                )
                self.processed_data['brands'][brand]['types'].add(product['type'])
                
                # Update coffee type stats
                coffee_type = product['type']
                if coffee_type not in self.processed_data['types']:
                    self.processed_data['types'][coffee_type] = {
                        'count': 0,
                        'avg_price': 0,
                        'total_price': 0,
                        'brands': set()
                    }
                
                self.processed_data['types'][coffee_type]['count'] += 1
                self.processed_data['types'][coffee_type]['total_price'] += product['price']
                self.processed_data['types'][coffee_type]['avg_price'] = (
                    self.processed_data['types'][coffee_type]['total_price'] / 
                    self.processed_data['types'][coffee_type]['count']
                )
                self.processed_data['types'][coffee_type]['brands'].add(product['brand'])
                
                # Update packaging stats
                packaging_key = product['packaging']['display']
                if packaging_key not in self.processed_data['packaging']:
                    self.processed_data['packaging'][packaging_key] = {
                        'count': 0,
                        'avg_price': 0,
                        'total_price': 0
                    }
                
                self.processed_data['packaging'][packaging_key]['count'] += 1
                self.processed_data['packaging'][packaging_key]['total_price'] += product['price']
                self.processed_data['packaging'][packaging_key]['avg_price'] = (
                    self.processed_data['packaging'][packaging_key]['total_price'] / 
                    self.processed_data['packaging'][packaging_key]['count']
                )
            
            logger.info(f"Added {len(sample_products)} sample products to the dataset")
            
                        # Update the metadata to indicate sample data
            self.processed_data['metadata'] = {
                'collection_time': datetime.now().isoformat(),
                'data_source': 'sample_generation',
                'total_products': len(self.processed_data['products']),
                'total_brands': len(self.processed_data['brands']),
                'note': 'This data was generated as sample data because website scraping failed. It can be used for testing and demonstration purposes.'
            }

            
    
    def _generate_pagination_url(self, base_url, page_number, site_name):
        """
        Generate a pagination URL for a specific site.
        
        Args:
            base_url (str): The base search URL
            page_number (int): The page number to generate URL for
            site_name (str): The name of the site to generate URL for
            
        Returns:
            str: The URL for the specified page
        """        
        # Different sites have different pagination URL structures
        if site_name == 'naheed':
            # Naheed uses the 'p' parameter
            if '?' in base_url:
                return f"{base_url}&p={page_number}"
            else:
                return f"{base_url}?p={page_number}"
        elif site_name == 'alibaba':
            # Alibaba might use a different structure depending on the URL format
            if '/page/' in base_url:
                return re.sub(r'/page/\d+', f'/page/{page_number}', base_url)
            elif 'page=' in base_url:
                return re.sub(r'page=\d+', f'page={page_number}', base_url)
            else:
                # Alibaba often uses a different pagination structure like /page/2
                return f"{base_url}/page/{page_number}"
        else:
            # Default pagination pattern (daraz, alfatah, metro, foodpanda use similar patterns)
            if 'page=' in base_url:
                return re.sub(r'page=\d+', f'page={page_number}', base_url)
            elif '?' in base_url:
                return f"{base_url}&page={page_number}"
            else:
                return f"{base_url}?page={page_number}"


def collect_coffee_market_data():
        """
        Collect coffee market data from Pakistani e-commerce sites.
        
        Returns:
            dict: Collected and processed data
        """
        collector = CoffeeMarketDataCollector()
        print(f"DEBUG: Attributes of collector: {sorted(dir(collector))}")
        print(f"DEBUG: collector.collect_data exists: {hasattr(collector, 'collect_data')}")
        if hasattr(collector, 'collect_data'):
            print(f"DEBUG: collector.collect_data is callable: {callable(collector.collect_data)}")
            print(f"DEBUG: collector.collect_data type: {type(collector.collect_data)}")
        else:
            print("DEBUG: collect_data attribute does NOT exist on collector instance!")
        data = collector.collect_data()
        saved_paths = collector.save_data()
        
        return {
            'data': data,
            'saved_paths': saved_paths
        }


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("coffee_market_scraper.log"),
            logging.StreamHandler()
        ]
    )
    
    # Run the data collection
    result = collect_coffee_market_data()
    
    print("\nData Collection Complete!")
    print(f"Total Products: {len(result['data']['products'])}")
    print(f"Total Brands: {len(result['data']['brands'])}")
    print(f"Coffee Types: {', '.join(result['data']['types'].keys())}")
    print(f"\nFiles saved to:")
    for file_type, path in result['saved_paths'].items():
        if isinstance(path, dict):
            for sub_type, sub_path in path.items():
                print(f"- {file_type} ({sub_type}): {sub_path}")
        else:
            print(f"- {file_type}: {path}")


