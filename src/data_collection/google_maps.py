"""
Module for collecting data from Google Maps using free resources.
This implementation uses web scraping to gather data about coffee shops.
"""

import os
import json
import logging
import time
import re
import random
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from ..config import TARGET_LOCATIONS, SEARCH_RADIUS, PATHS

logger = logging.getLogger(__name__)

class GoogleMapsDataCollector:
    """Class to handle collection of coffee shop data from Google Maps using web scraping."""
    
    def __init__(self):
        """Initialize the collector with web scraping setup."""
        self.driver = None
        self.wait = None
    
    def setup_selenium(self):
        """Set up Selenium WebDriver for scraping."""
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            
            # Use webdriver-manager to handle driver setup
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("Selenium WebDriver set up successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up Selenium WebDriver: {str(e)}")
            return False
            
    def search_coffee_shops(self, location, radius=SEARCH_RADIUS):
        """
        Search for coffee shops in a given location.
        
        Args:
            location (str): Location string (e.g., "Karachi, Pakistan")
            radius (int): Search radius in meters (not directly used in this implementation)
            
        Returns:
            list: List of coffee shops with their basic details
        """
        logger.info(f"Searching for coffee shops in {location}")
        
        if self.driver is None:
            if not self.setup_selenium():
                logger.error("WebDriver setup failed, cannot search for coffee shops")
                return []
        
        coffee_shops = []
        query = f"coffee shops in {location}"
        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        
        try:
            # Add a random delay before request to avoid triggering anti-bot measures
            time.sleep(random.uniform(1.0, 3.0))
            
            self.driver.get(search_url)
            
            # Wait for search results to load
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']")))
            except TimeoutException:
                logger.error(f"Timeout waiting for search results in {location}")
                
                # Take a screenshot of the failure for debugging
                screenshot_path = f"error_screenshot_{location.replace(' ', '_')}_{int(time.time())}.png"
                try:
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Error screenshot saved to {screenshot_path}")
                except Exception as ss_e:
                    logger.error(f"Failed to save error screenshot: {str(ss_e)}")
                
                # Check if we hit a CAPTCHA
                if "captcha" in self.driver.page_source.lower() or "verify you're a human" in self.driver.page_source.lower():
                    logger.warning("CAPTCHA detected, might need manual intervention")
                
                return []
            
            # Let the page load completely (some elements load dynamically)
            time.sleep(3)
            
            # Get initial results
            coffee_shops = self._extract_search_results(location)
            
            # Scroll to load more results (typically loads about 20 results per scroll)
            for i in range(3):  # Try to scroll 3 times to get more results
                self._scroll_page()
                
                # Random delay between scrolls
                time.sleep(random.uniform(1.5, 3.5))
                
                new_results = self._extract_search_results(location)
                
                # Add only new shops (that aren't already in our list)
                existing_ids = {shop['place_id'] for shop in coffee_shops}
                new_shops = [shop for shop in new_results if shop['place_id'] not in existing_ids]
                coffee_shops.extend(new_shops)
                
                logger.info(f"Scroll {i+1}: Found {len(new_shops)} new coffee shops in {location}, total: {len(coffee_shops)}")
                
                # If no new results after scrolling, we've probably reached the end
                if not new_shops:
                    logger.info("No new results after scrolling, stopping pagination")
                    break
            
        except Exception as e:
            logger.error(f"Error searching for coffee shops in {location}: {str(e)}")
            
        return coffee_shops
        
    def _extract_search_results(self, location):
        """
        Extract coffee shop data from the current search results page.
        
        Args:
            location (str): Location string for the search
            
        Returns:
            list: List of coffee shops with basic details
        """
        coffee_shops = []
        
        try:
            # Find all search result elements
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
            
            for element in result_elements:
                try:
                    # Try to extract place_id from data attributes
                    place_id = None
                    try:
                        # This is a complex part as Google's structure changes frequently
                        # We'll try to get it from various attributes
                        element_html = element.get_attribute('innerHTML')
                        # Try to find data-place-id or similar attribute
                        place_id_match = re.search(r'data-place-id="([^"]+)"', element_html)
                        if place_id_match:
                            place_id = place_id_match.group(1)
                        else:
                            # Generate a pseudo-id from shop name and address
                            name_element = element.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall")
                            if name_element:
                                place_id = f"pseudo-{name_element.text}-{int(time.time())}"
                    except:
                        # If we can't get an ID, generate a temporary one
                        place_id = f"temp-id-{len(coffee_shops)}-{int(time.time())}"
                    
                    # Extract name
                    name = ""
                    try:
                        name_element = element.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall")
                        name = name_element.text
                    except:
                        pass
                    
                    # Extract address
                    address = ""
                    try:
                        # Address is often in the second or third line of info
                        info_elements = element.find_elements(By.CSS_SELECTOR, "div.fontBodyMedium > div")
                        if len(info_elements) >= 2:
                            address = info_elements[1].text
                    except:
                        pass
                    
                    # Extract rating
                    rating = None
                    rating_count = None
                    try:
                        rating_text = element.find_element(By.CSS_SELECTOR, "span.fontBodyMedium > span").text
                        if rating_text:
                            rating_parts = rating_text.split('(')
                            if len(rating_parts) >= 1:
                                try:
                                    rating = float(rating_parts[0].strip())
                                except:
                                    pass
                            if len(rating_parts) >= 2:
                                try:
                                    rating_count = int(rating_parts[1].replace(')', '').replace(',', '').strip())
                                except:
                                    pass
                    except:
                        pass
                    
                    # Extract price level
                    price_level = None
                    try:
                        price_text = ""
                        info_elements = element.find_elements(By.CSS_SELECTOR, "div.fontBodyMedium > div")
                        for info in info_elements:
                            if '$$' in info.text:
                                price_text = info.text
                                break
                        
                        if price_text:
                            if '$$$$' in price_text:
                                price_level = 4
                            elif '$$$' in price_text:
                                price_level = 3
                            elif '$$' in price_text:
                                price_level = 2
                            elif '$' in price_text:
                                price_level = 1
                    except:
                        pass
                    
                    # Only add shop if we have at least a name
                    if name:
                        shop = {
                            'place_id': place_id,
                            'name': name,
                            'address': address,
                            'location': location,
                            'rating': rating,
                            'user_ratings_total': rating_count,
                            'price_level': price_level
                        }
                        coffee_shops.append(shop)
                
                except Exception as e:
                    logger.warning(f"Error extracting coffee shop data: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting search results: {str(e)}")
        
        return coffee_shops
    
    def _scroll_page(self):
        """Scroll down to load more search results."""
        try:
            # Find the scrollable element that contains the search results
            scrollable = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
            return True
        except:
            # If that fails, try to scroll the whole window            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            return True
            
    def get_place_details(self, place_id):
        """
        Get detailed information about a place.
        
        Args:
            place_id (str): Google Place ID (or pseudo-ID from search results)
            
        Returns:
            dict: Details of the place
        """
        logger.info(f"Getting details for place {place_id}")
        
        if self.driver is None:
            if not self.setup_selenium():
                logger.error("WebDriver setup failed, cannot get place details")
                return {}
        
        # Check if it's a pseudo-id (generated from search results)
        if place_id.startswith('pseudo-') or place_id.startswith('temp-id'):
            # We don't have a real place_id, so we can't get more details
            # Just return whatever we already have
            logger.warning(f"Cannot get additional details for place with pseudo-id: {place_id}")
            return {}
        
        # Add random delay to avoid triggering anti-scraping measures
        time.sleep(random.uniform(2.0, 4.0))
        
        try:
            # Navigate to the place's page
            place_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            self.driver.get(place_url)
            
            # Check for CAPTCHA before proceeding
            if "captcha" in self.driver.page_source.lower() or "verify you're a human" in self.driver.page_source.lower():
                logger.warning(f"CAPTCHA detected when accessing place {place_id}, taking screenshot")
                
                # Take a screenshot of the CAPTCHA
                screenshot_path = f"captcha_screenshot_{place_id}_{int(time.time())}.png"
                try:
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"CAPTCHA screenshot saved to {screenshot_path}")
                except Exception as ss_e:
                    logger.error(f"Failed to save CAPTCHA screenshot: {str(ss_e)}")
                
                # Since we hit a CAPTCHA, we need to pause and potentially reset our session
                logger.info("Waiting 30 seconds before continuing...")
                time.sleep(30)  # Wait longer to avoid immediate retries that might trigger more CAPTCHAs
                
                # Return empty details
                return {}
            
            # Wait for the page to load
            try:
                # Wait for a common element to indicate the page is loaded
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.fontHeadlineLarge")))
            except TimeoutException:
                logger.error(f"Timeout waiting for details page to load for place {place_id}")
                return {}
            
            # Wait a bit longer for dynamic elements
            time.sleep(2)
            
            # Extract details
            details = {}
            
            # Name
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, "h1.fontHeadlineLarge")
                details['name'] = name_element.text
            except Exception as e:
                logger.warning(f"Error extracting name for place {place_id}: {str(e)}")
                pass
            
            # Address
            try:
                address_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-item-id='address']")
                if address_elements:
                    details['address'] = address_elements[0].text
            except Exception as e:
                logger.warning(f"Error extracting address for place {place_id}: {str(e)}")
                pass
            
            # Website
            try:
                website_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[data-item-id='authority']")
                if website_elements:
                    details['website'] = website_elements[0].get_attribute('href')
            except Exception as e:
                logger.warning(f"Error extracting website for place {place_id}: {str(e)}")
                pass
            
            # Phone
            try:
                phone_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-item-id^='phone:']")
                if phone_elements:
                    details['phone'] = phone_elements[0].text
            except Exception as e:
                logger.warning(f"Error extracting phone for place {place_id}: {str(e)}")
                pass
            
            # Opening hours
            try:
                # Try to click on the "See more hours" button if it exists
                try:
                    hours_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'See more hours') or contains(text(), 'More hours')]")
                    if hours_buttons:
                        hours_buttons[0].click()
                        time.sleep(1)  # Wait for hours to expand
                except:
                    pass
                
                # Now try to extract hours
                hours_elements = self.driver.find_elements(By.CSS_SELECTOR, "table.eK4R0e")
                if hours_elements:
                    hours_rows = hours_elements[0].find_elements(By.CSS_SELECTOR, "tr")
                    opening_hours = []
                    
                    for row in hours_rows:
                        try:
                            day_element = row.find_element(By.CSS_SELECTOR, "td:first-child")
                            hours_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)")
                            
                            opening_hours.append({
                                'day': day_element.text.strip(),
                                'hours': hours_element.text.strip()
                            })
                        except:
                            continue
                    
                    details['opening_hours'] = opening_hours
            except Exception as e:
                logger.warning(f"Error extracting opening hours for place {place_id}: {str(e)}")
                pass
            
            # Reviews
            try:
                # Try clicking on reviews tab
                try:
                    review_tabs = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Reviews')]")
                    if review_tabs:
                        review_tabs[0].click()
                        time.sleep(2)  # Wait for reviews to load
                except:
                    pass
                
                # Extract reviews
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
                reviews = []
                
                for i, review_element in enumerate(review_elements[:10]):  # Limit to 10 reviews
                    try:
                        # Author
                        author_element = review_element.find_element(By.CSS_SELECTOR, "div.d4r55")
                        author = author_element.text
                        
                        # Rating
                        rating_element = review_element.find_element(By.CSS_SELECTOR, "span.kvMYJc")
                        rating_style = rating_element.get_attribute("style")
                        # Extract rating from style (width is proportional to rating)
                        rating_match = re.search(r'width:\s*(\d+)px', rating_style)
                        rating = 5
                        if rating_match:
                            width = int(rating_match.group(1))
                            rating = round((width / 65) * 5, 1)  # 65px is full width (5 stars)
                            
                        # Review date
                        date_element = review_element.find_element(By.CSS_SELECTOR, "span.rsqaWe")
                        date_text = date_element.text
                        
                        # Review text
                        text_element = review_element.find_element(By.CSS_SELECTOR, "span.wiI7pd")
                        text = text_element.text
                        
                        reviews.append({
                            'author_name': author,
                            'rating': rating,
                            'relative_time_description': date_text,
                            'text': text
                        })
                    except Exception as e:
                        logger.warning(f"Error extracting review #{i} for place {place_id}: {str(e)}")
                        continue
                
                if reviews:
                    details['reviews'] = reviews
            except Exception as e:
                logger.warning(f"Error extracting reviews for place {place_id}: {str(e)}")
                pass
            
            # Popular times
            try:
                popular_times = {}
                popular_times_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g2BVhd")
                
                if popular_times_elements:
                    # Click on "See more hours" if available to view popular times
                    try:
                        see_more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'See popular times')]")
                        if see_more_buttons:
                            see_more_buttons[0].click()
                            time.sleep(1)
                    except:
                        pass
                    
                    # Extract popular times data
                    days_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g2BVhd")
                    
                    for day_idx, day_element in enumerate(days_elements):
                        try:
                            day_name_element = day_element.find_element(By.CSS_SELECTOR, "div.y0skZc")
                            day_name = day_name_element.text.strip()
                            
                            hour_elements = day_element.find_elements(By.CSS_SELECTOR, "div.dpoVLd")
                            hours_data = []
                            
                            for hour_idx, hour_element in enumerate(hour_elements):
                                try:
                                    # Height attribute indicates popularity (0-100%)
                                    popularity_bar = hour_element.find_element(By.CSS_SELECTOR, "div.kwVK4b")
                                    popularity_style = popularity_bar.get_attribute("style")
                                    
                                    # Extract height percentage
                                    pop_match = re.search(r'height:\s*(\d+)%', popularity_style)
                                    popularity = 0
                                    if pop_match:
                                        popularity = int(pop_match.group(1))
                                    
                                    # Calculate approximate hour (6am to 12am range)
                                    hour = 6 + hour_idx  # Assuming the first bar is 6am
                                    
                                    hours_data.append({
                                        'hour': hour,
                                        'popularity': popularity
                                    })
                                except:
                                    continue
                            
                            if day_name and hours_data:
                                popular_times[day_name] = hours_data
                        except:
                            continue
                    
                    if popular_times:
                        details['popular_times'] = popular_times
            except Exception as e:
                logger.warning(f"Error extracting popular times for place {place_id}: {str(e)}")
                pass
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting details for place {place_id}: {str(e)}")
            return {}
    
    def get_popular_times_from_page(self):
        """
        Extract popular times data from the current page.
        
        Returns:
            dict: Popular times data if available, otherwise None
        """
        try:
            # Look for the popular times section
            popular_times_section = self.driver.find_elements(By.CSS_SELECTOR, "div[aria-label*='Popular times']")
            
            if not popular_times_section:
                return None
            
            # This is challenging to extract as Google's structure for popular times changes often
            # and doesn't have consistent class names or attributes
            # This is a simplified approach that may need adjustments
            
            # Try to extract day names
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            popular_times_data = {}
            
            # Click through each day tab
            for day in days:
                try:
                    # Find and click the day tab
                    day_tab = None
                    day_tabs = self.driver.find_elements(By.CSS_SELECTOR, "button[role='tab']")
                    
                    for tab in day_tabs:
                        if day.lower() in tab.text.lower():
                            day_tab = tab
                            break
                    
                    if day_tab:
                        day_tab.click()
                        time.sleep(0.5)
                        
                        # Try to extract hour data
                        # This part is highly dependent on Google's current DOM structure
                        # and may need adjustments
                        hour_data = []
                        hour_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='graphics-datavisualization'] div")
                        
                        # Logic to parse the bars representing busyness at each hour
                        # This is a simplified approximation
                        current_hour = 6  # Typical start hour
                        
                        for element in hour_elements:
                            try:
                                style = element.get_attribute("style")
                                if "height:" in style:
                                    # Extract height percentage as approximation of busyness
                                    height_match = re.search(r'height:\s*(\d+)%', style)
                                    if height_match:
                                        height_pct = int(height_match.group(1))
                                        hour_data.append({
                                            "hour": current_hour,
                                            "occupancy_percentage": height_pct
                                        })
                                        current_hour += 1
                                        if current_hour >= 24:
                                            break
                            except:
                                continue
                        
                        if hour_data:
                            popular_times_data[day.lower()] = hour_data
                except:
                    pass
            
            return popular_times_data if popular_times_data else None
            
        except Exception as e:
            logger.warning(f"Error extracting popular times: {str(e)}")
            return None
    
    def process_shop_data(self, basic_data, detailed_data):
        """
        Process and combine basic and detailed data into a structured format.
        
        Args:
            basic_data (dict): Basic shop data from search results
            detailed_data (dict): Detailed shop data from place details
            
        Returns:
            dict: Processed coffee shop data
        """
        # Combine data, with detailed data taking precedence
        shop_data = {**basic_data, **detailed_data}
        
        processed_data = {
            'place_id': shop_data.get('place_id'),
            'name': shop_data.get('name'),
            'address': shop_data.get('address'),
            'location': shop_data.get('location'),  # This would be the city name
            'lat': None,  # We don't have precise coordinates from scraping
            'lng': None,  # We don't have precise coordinates from scraping
            'rating': shop_data.get('rating'),
            'user_ratings_total': shop_data.get('user_ratings_total'),
            'price_level': shop_data.get('price_level'),
            'website': shop_data.get('website'),
            'phone': shop_data.get('phone'),
            'opening_hours': shop_data.get('opening_hours', []),
            'reviews': shop_data.get('reviews', []),
            'popular_times': shop_data.get('popular_times'),
            'data_source': 'google_maps_scraper',
            'collected_at': datetime.now().isoformat()
        }
        return processed_data
        
def close(self):
        """Close the WebDriver session."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver session closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver session: {str(e)}")


def collect_google_maps_data():
    """
    Collect coffee shop data from Google Maps using web scraping.
    
    Returns:
        list: Collected coffee shop data
    """
    collector = GoogleMapsDataCollector()
    all_coffee_shops = []
    
    # Create a data directory if it doesn't exist
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(base_dir, PATHS['raw_data'])
    os.makedirs(output_dir, exist_ok=True)
    
    # Set a timestamp for this collection run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Track progress of data collection
        total_locations = len(TARGET_LOCATIONS)
        processed_locations = 0
        
        logger.info(f"Starting coffee shop data collection for {total_locations} locations")
        
        # Create a log directory for screenshots
        screenshot_dir = os.path.join(output_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        for location in TARGET_LOCATIONS:
            processed_locations += 1
            logger.info(f"[{processed_locations}/{total_locations}] Collecting data for location: {location}")
            
            try:
                # Collect basic shop information
                shops = collector.search_coffee_shops(location)
                logger.info(f"Found {len(shops)} coffee shops in {location}")
                
                # Process each shop and get additional details
                processed_count = 0
                for shop in shops:
                    place_id = shop.get('place_id')
                    if not place_id:
                        continue
                    
                    try:
                        # Skip places with pseudo IDs as we can't get more details
                        if place_id.startswith('pseudo-') or place_id.startswith('temp-id'):
                            processed_data = collector.process_shop_data(shop, {})
                            all_coffee_shops.append(processed_data)
                        else:
                            # Rate limiting: pause between requests
                            if processed_count > 0 and processed_count % 5 == 0:
                                sleep_time = random.uniform(10.0, 15.0)
                                logger.info(f"Taking a break for {sleep_time:.1f} seconds to avoid rate limiting...")
                                time.sleep(sleep_time)
                            
                            logger.info(f"Getting details for shop: {shop.get('name')} (ID: {place_id})")
                            details = collector.get_place_details(place_id)
                            
                            if details:
                                processed_data = collector.process_shop_data(shop, details)
                                all_coffee_shops.append(processed_data)
                                processed_count += 1
                                
                                # Save partial results periodically
                                if len(all_coffee_shops) % 10 == 0:
                                    # Save current progress to a temporary file
                                    temp_file = os.path.join(output_dir, f"google_maps_partial_{timestamp}.json")
                                    with open(temp_file, 'w', encoding='utf-8') as f:
                                        json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
                                    logger.info(f"Saved partial data ({len(all_coffee_shops)} shops) to {temp_file}")
                    
                    except Exception as e:
                        logger.error(f"Error processing shop {shop.get('name', 'Unknown')}: {str(e)}")
                        # Continue with next shop
                        continue
                
                # Take a longer break between locations to avoid triggering anti-scraping measures
                if processed_locations < total_locations:
                    pause_time = random.uniform(15.0, 30.0)
                    logger.info(f"Completed collection for {location}. Taking a {pause_time:.1f} second break before next location...")
                    time.sleep(pause_time)
                
            except Exception as e:
                logger.error(f"Error collecting data for location {location}: {str(e)}")
                # Continue with next location
                continue
        
        # Final data save
        output_file = os.path.join(output_dir, f"google_maps_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
        
        # Also save a 'latest' copy for easy access
        latest_file = os.path.join(output_dir, "google_maps_latest.json")
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Saved {len(all_coffee_shops)} coffee shops data to {output_file}")
        
    except Exception as e:
        logger.error(f"Error in coffee shop data collection: {str(e)}")
        
        # Try to save whatever data we've collected so far
        if all_coffee_shops:
            try:
                error_file = os.path.join(output_dir, f"google_maps_error_recovery_{timestamp}.json")
                with open(error_file, 'w', encoding='utf-8') as f:
                    json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
                logger.info(f"Saved {len(all_coffee_shops)} coffee shops to error recovery file {error_file}")
            except:
                logger.error("Failed to save error recovery file")
    
    finally:
        # Make sure to close the WebDriver session
        try:
            collector.close()
        except Exception as e:
            logger.error(f"Error closing WebDriver session: {str(e)}")
    
    return all_coffee_shops


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Collect data
    collect_google_maps_data()
    
    def get_popular_times(self, place_id):
        """
        Get popular times data for a place.
        Note: This is a workaround since the direct popular times data is not 
        part of the official Places API. In a real implementation, you might use 
        a third-party service or implement web scraping.
        
        Args:
            place_id (str): Google Place ID
            
        Returns:
            dict: Popular times data if available
        """
        # This is a placeholder. In a real implementation, you would implement proper logic
        # to obtain this data, possibly through scraping or a third-party service
        logger.warning(f"Popular times data retrieval not implemented for {place_id}")
        
        # Return dummy data for demonstration
        return {
            "monday": [
                {"hour": 6, "occupancy_percentage": 0},
                {"hour": 7, "occupancy_percentage": 5},
                {"hour": 8, "occupancy_percentage": 30},
                {"hour": 9, "occupancy_percentage": 60},
                # ... and so on
            ],
            # More days would follow...
        }
    
    def process_shop_data(self, place_data):
        """
        Process raw place data into a structured format.
        
        Args:
            place_data (dict): Raw place data
            
        Returns:
            dict: Processed coffee shop data
        """
        photos = place_data.get('photos', [])
        photo_references = [photo.get('photo_reference') for photo in photos if 'photo_reference' in photo]
        photo_urls = self.get_place_photos(photo_references)
        
        reviews = place_data.get('reviews', [])
        processed_reviews = []
        
        for review in reviews:
            processed_reviews.append({
                'rating': review.get('rating'),
                'text': review.get('text'),
                'time': review.get('time'),
                'author_name': review.get('author_name')
            })
        
        return {
            'place_id': place_data.get('place_id'),
            'name': place_data.get('name'),
            'address': place_data.get('formatted_address'),
            'location': {
                'lat': place_data.get('geometry', {}).get('location', {}).get('lat'),
                'lng': place_data.get('geometry', {}).get('location', {}).get('lng')
            },
            'rating': place_data.get('rating'),
            'user_ratings_total': place_data.get('user_ratings_total'),
            'price_level': place_data.get('price_level'),
            'website': place_data.get('website'),
            'phone': place_data.get('formatted_phone_number'),
            'opening_hours': place_data.get('opening_hours', {}).get('weekday_text', []),
            'photos': photo_urls,
            'reviews': processed_reviews,
            'google_maps_url': place_data.get('url'),
            'popular_times': self.get_popular_times(place_data.get('place_id')),
            'data_source': 'google_maps',
            'collected_at': datetime.now().isoformat()
        }


def collect_google_maps_data():
    """
    Collect coffee shop data from Google Maps.
    
    Returns:
        list: Collected coffee shop data
    """
    collector = GoogleMapsDataCollector()
    all_coffee_shops = []
    
    for location in TARGET_LOCATIONS:
        logger.info(f"Collecting data for location: {location}")
        shops = collector.search_coffee_shops(location)
        
        for shop in shops:
            place_id = shop.get('place_id')
            if place_id:
                details = collector.get_place_details(place_id)
                if details:
                    # Combine basic search result with detailed information
                    shop_data = {**shop, **details}
                    processed_data = collector.process_shop_data(shop_data)
                    all_coffee_shops.append(processed_data)
    
    # Save raw data to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), PATHS['raw_data'])
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"google_maps_{timestamp}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Saved {len(all_coffee_shops)} coffee shops data to {output_file}")
    
    return all_coffee_shops


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Collect data
    collect_google_maps_data()
