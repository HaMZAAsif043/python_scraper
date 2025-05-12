import os
import json
import time
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import configuration from the project
from src.config import TARGET_LOCATIONS, PATHS

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Optional: Hide automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Return the driver
    return webdriver.Chrome(options=options)

def search_coffee_shops(driver, location, scroll_count=5):
    """
    Search for coffee shops in the given location.
    
    Args:
        driver: Selenium WebDriver
        location: Location string (e.g., "Lahore, Pakistan")
        scroll_count: Number of times to scroll results
        
    Returns:
        List of coffee shop data dictionaries
    """
    print(f"Searching for coffee shops in {location}...")
    
    # Go to Google Maps
    driver.get("https://www.google.com/maps")
    time.sleep(3)
    
    # Search for coffee shops
    try:
        search_input = driver.find_element(By.ID, "searchboxinput")
        search_input.clear()
        search_input.send_keys(f"coffee shops in {location}")
        search_input.send_keys(Keys.ENTER)
        
        # Wait for results to load
        print("Waiting for search results...")
        time.sleep(10)
        
        # Scroll the results panel to load more
        try:
            print(f"Scrolling to load more results ({scroll_count} scrolls)...")
            scrollable = driver.find_element(By.XPATH, '//div[@role="feed"]')
            for i in range(scroll_count):
                print(f"Scroll {i+1}/{scroll_count}")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
                time.sleep(2 + random.random())  # Add random delay
        except Exception as e:
            print(f"Error scrolling: {e}")
        
        # Find all place elements
        print("Extracting place data...")
        coffee_shops = []
        places = driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
        
        for i, place in enumerate(places):
            try:
                name = place.get_attribute('aria-label')
                link = place.get_attribute('href')
                
                # Extract place_id from the link
                place_id = None
                if link:
                    place_id_match = re.search(r'place/[^/]+/([^?]+)', link)
                    if place_id_match:
                        place_id = place_id_match.group(1)
                    else:
                        # Generate a pseudo ID if we can't extract one
                        place_id = f"pseudo-{i}-{int(time.time())}"
                
                if name and link:
                    print(f"Found place: {name}")
                    
                    # Find the parent element to extract additional data
                    parent_el = place.find_element(By.XPATH, './../../..')
                    
                    # Try to extract rating
                    rating = None
                    rating_count = None
                    try:
                        rating_el = parent_el.find_element(By.CSS_SELECTOR, 'span.MW4etd')
                        if rating_el:
                            rating = float(rating_el.text)
                            
                        # Try to get the number of reviews
                        review_count_el = parent_el.find_element(By.CSS_SELECTOR, 'span.UY7F9')
                        if review_count_el:
                            # Extract numbers from text like "(123)"
                            count_match = re.search(r'\((\d+)\)', review_count_el.text)
                            if count_match:
                                rating_count = int(count_match.group(1))
                    except:
                        pass  # Rating info not available
                    
                    # Extract address
                    address = ""
                    try:
                        # First try with specific selector
                        address_els = parent_el.find_elements(By.CSS_SELECTOR, '.W4Efsd:nth-child(2) .W4Efsd:nth-child(1) span:not(.MW4etd):not(.UY7F9)')
                        if address_els:
                            address = address_els[0].text
                    except:
                        pass
                    
                    # Extract the price level
                    price_level = None
                    try:
                        price_el = parent_el.find_elements(By.CSS_SELECTOR, '.W4Efsd span')
                        for el in price_el:
                            if '$' in el.text:
                                price_str = el.text
                                price_level = price_str.count('$')
                                break
                    except:
                        pass
                    
                    # Create a shop object
                    shop = {
                        'place_id': place_id,
                        'name': name,
                        'address': address,
                        'location': location,
                        'rating': rating,
                        'user_ratings_total': rating_count,
                        'price_level': price_level,
                        'url': link,
                        'data_source': 'google_maps_scraper',
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    coffee_shops.append(shop)
            except Exception as e:
                print(f"Error extracting data for a place: {e}")
        
        return coffee_shops
    
    except Exception as e:
        print(f"Error during search: {e}")
        # Save a screenshot for debugging
        screenshot_path = f"error_screenshot_{location.replace(' ', '_').replace(',', '_')}_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Error screenshot saved to {screenshot_path}")
        return []

def collect_and_save_data():
    """Collect coffee shop data for all target locations and save to a JSON file."""
    driver = setup_driver()
    all_coffee_shops = []
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        for location in TARGET_LOCATIONS:
            print(f"\n=== Processing location: {location} ===")
            
            # Add a random delay between locations
            if location != TARGET_LOCATIONS[0]:  # Skip delay for first location
                delay = random.uniform(5, 10)
                print(f"Waiting {delay:.1f} seconds before next location...")
                time.sleep(delay)
            
            # Collect data for this location
            shops = search_coffee_shops(driver, location)
            all_coffee_shops.extend(shops)
            
            print(f"Found {len(shops)} coffee shops in {location}")
            print(f"Total coffee shops collected so far: {len(all_coffee_shops)}")
        
        # Create output directory if it doesn't exist
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, PATHS['raw_data'])
        os.makedirs(output_dir, exist_ok=True)
        
        # Save data to JSON file
        output_file = os.path.join(output_dir, f"google_maps_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
        
        # Also save a 'latest' copy for easy access
        latest_file = os.path.join(output_dir, "google_maps_latest.json")
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
        
        print(f"\n=== Collection complete! ===")
        print(f"Collected data for {len(all_coffee_shops)} coffee shops")
        print(f"Data saved to: {output_file}")
        
        return all_coffee_shops
    
    except Exception as e:
        print(f"Error during data collection: {e}")
        return []
    
    finally:
        # Always close the driver
        print("Closing WebDriver...")
        driver.quit()

if __name__ == "__main__":
    print("Starting coffee shop data collection...")
    collect_and_save_data()
