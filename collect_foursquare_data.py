import os
import json
import time
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import configuration from the project
from src.config import TARGET_LOCATIONS, PATHS

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    options = Options()
    options.add_argument("--start-maximized")
    # Optional: Hide automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Return the driver
    return webdriver.Chrome(options=options)

def search_coffee_shops_foursquare(driver, location, max_scrolls=5):
    """
    Search for coffee shops in the given location using Foursquare.
    
    Args:
        driver: Selenium WebDriver
        location: Location string (e.g., "Lahore, Pakistan")
        max_scrolls: Number of times to scroll to load more results
        
    Returns:
        List of coffee shop data dictionaries
    """
    print(f"Searching for coffee shops in {location} on Foursquare...")
    
    # Extract the city name without country
    city = location.split(',')[0].strip()
    
    # Go to Foursquare search page for coffee in the specified city
    url = f"https://foursquare.com/explore?mode=url&near={city}%2C%20Pakistan&nearGeoId=72057594040090834&q=Coffee"
    driver.get(url)
    
    # Wait for the page to load
    print("Waiting for search results...")
    time.sleep(5)
    
    # Check for cookie/consent dialogs and close them if present
    try:
        consent_buttons = driver.find_elements(By.XPATH, 
            "//button[contains(text(), 'Accept') or contains(text(), 'I Agree') or contains(text(), 'OK') or contains(text(), 'Got it')]")
        if consent_buttons:
            consent_buttons[0].click()
            print("Closed consent dialog")
            time.sleep(2)
    except:
        print("No consent dialog found or unable to close it")
    
    # Scroll the page to load more results
    print(f"Scrolling to load more results ({max_scrolls} scrolls)...")
    for i in range(max_scrolls):
        print(f"Scroll {i+1}/{max_scrolls}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2 + random.random())  # Add random delay
    
    # Now extract the coffee shop data
    coffee_shops = []
    
    # On Foursquare, venue cards are typically contained in list items
    try:
        # Various selectors to try for venue cards
        selectors = [
            "div[data-testid='venue-card']",
            "div.venue-card",
            "div.venueCard",
            "div[data-test-id='venue-card']",
            "li.venue-card",
            "article.venue",
            "div.venue_cardContainer"
        ]
        
        venue_elements = []
        for selector in selectors:
            venue_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if venue_elements:
                print(f"Found {len(venue_elements)} venues using selector: {selector}")
                break
        
        if not venue_elements:
            print("Couldn't find venue elements with predefined selectors")
            # Take a screenshot for debugging
            screenshot_path = f"foursquare_error_{city.replace(' ', '_')}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            return []
        
        print(f"Found {len(venue_elements)} coffee shops")
        
        for i, venue in enumerate(venue_elements):
            try:
                # Extract name
                name = ""
                try:
                    name_elements = venue.find_elements(By.CSS_SELECTOR, "h2, h3, .venue-name, [data-testid='venue-name']")
                    if name_elements:
                        name = name_elements[0].text.strip()
                except:
                    pass
                
                # Extract URL
                url = ""
                try:
                    link_elements = venue.find_elements(By.TAG_NAME, "a")
                    if link_elements:
                        url = link_elements[0].get_attribute('href')
                except:
                    pass
                
                # Extract rating
                rating = None
                try:
                    rating_elements = venue.find_elements(By.CSS_SELECTOR, ".venue-rating, [data-testid='venue-rating']")
                    if rating_elements:
                        rating_text = rating_elements[0].text.strip()
                        # Extract number from text like "8.5" or "8,5"
                        rating_match = re.search(r'(\d+[.,]\d+)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1).replace(',', '.'))
                except:
                    pass
                
                # Extract address
                address = ""
                try:
                    address_elements = venue.find_elements(By.CSS_SELECTOR, ".venue-address, [data-testid='venue-address']")
                    if address_elements:
                        address = address_elements[0].text.strip()
                except:
                    pass
                
                # Extract price level
                price_level = None
                try:
                    price_elements = venue.find_elements(By.CSS_SELECTOR, ".venue-price, [data-testid='venue-price']")
                    if price_elements:
                        price_text = price_elements[0].text.strip()
                        price_level = price_text.count('$')
                except:
                    pass
                
                # Only add shops with at least a name
                if name:
                    shop_data = {
                        'place_id': f"fsq-{i}-{int(time.time())}",  # Generate a pseudo-ID
                        'name': name,
                        'address': address,
                        'location': location,
                        'rating': rating,
                        'price_level': price_level,
                        'url': url,
                        'data_source': 'foursquare_scraper',
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    coffee_shops.append(shop_data)
                    print(f"Added shop: {name}")
            
            except Exception as e:
                print(f"Error extracting data for venue #{i}: {e}")
                continue
        
    except Exception as e:
        print(f"Error during Foursquare data extraction: {e}")
        # Take a screenshot for debugging
        screenshot_path = f"foursquare_error_{city.replace(' ', '_')}_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Error screenshot saved to {screenshot_path}")
    
    return coffee_shops

def collect_and_save_foursquare_data():
    """Collect coffee shop data from Foursquare for all target locations and save to a JSON file."""
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
            shops = search_coffee_shops_foursquare(driver, location)
            all_coffee_shops.extend(shops)
            
            print(f"Found {len(shops)} coffee shops in {location}")
            print(f"Total coffee shops collected so far: {len(all_coffee_shops)}")
        
        # Create output directory if it doesn't exist
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, PATHS['raw_data'])
        os.makedirs(output_dir, exist_ok=True)
        
        # Save data to JSON file
        output_file = os.path.join(output_dir, f"foursquare_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
        
        # Also save a 'latest' copy for easy access
        latest_file = os.path.join(output_dir, "foursquare_latest.json")
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
    print("Starting Foursquare coffee shop data collection...")
    collect_and_save_foursquare_data()
