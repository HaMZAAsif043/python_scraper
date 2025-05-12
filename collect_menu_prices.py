import os
import json
import time
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
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

def extract_menu_items(text):
    """
    Extract menu items and prices from text.
    Looks for patterns like:
    - Cappuccino - Rs. 300
    - Latte (Regular) Rs.350
    - Americano Rs 250
    """
    menu_items = []
    
    # Common coffee types to look for
    coffee_types = [
        'americano', 'cappuccino', 'espresso', 'latte', 'mocha', 'macchiato',
        'flat white', 'cold brew', 'frappuccino', 'coffee', 'decaf',
        'affogato', 'cortado', 'ristretto'
    ]
    
    # Pattern for price - handles different formats: Rs. 300, Rs 300, PKR 300, 300 Rs
    price_pattern = r'(?:rs\.?|pkr|pk|rs)[^\d]*(\d+)|(\d+)[^\d]*(?:rs\.?|pkr)'
    
    # Split text into lines
    lines = text.lower().split('\n')
    
    for line in lines:
        for coffee_type in coffee_types:
            if coffee_type in line:
                # Try to extract the price
                price_match = re.search(price_pattern, line.lower())
                if price_match:
                    # Get the captured price from whichever group matched
                    price_str = price_match.group(1) if price_match.group(1) else price_match.group(2)
                    price = f"Rs. {price_str}"
                    
                    # Clean the item name (get the original case from the line)
                    item_name_match = re.search(f"(.*{coffee_type}.*?)(?:rs\.?|pkr|pk|rs|\\d)", line.lower())
                    if item_name_match:
                        item_name = item_name_match.group(1).strip()
                        # Get original case
                        original_line = line.split('\n')[0] if '\n' in line else line
                        start_idx = original_line.lower().find(item_name)
                        if start_idx != -1:
                            item_name = original_line[start_idx:start_idx+len(item_name)].strip()
                    else:
                        # Just use the coffee type with proper capitalization
                        item_name = coffee_type.capitalize()
                    
                    menu_items.append({
                        "name": item_name,
                        "price": price,
                        "description": ""
                    })
                    break  # Found a match for this line, move to next line
    
    return menu_items

def collect_menu_from_google_maps(driver, place_id):
    """
    Collect menu information from a Google Maps place page.
    
    Args:
        driver: Selenium WebDriver
        place_id: The Google Maps place ID
        
    Returns:
        List of menu items with prices
    """
    menu_items = []
    
    try:
        # Construct URL for the place
        url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        driver.get(url)
        
        # Wait for the place to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.fontHeadlineLarge"))
        )
        
        print(f"Collecting menu for: {driver.title}")
        
        # Expand the menu section if available
        try:
            menu_sections = driver.find_elements(By.XPATH, "//button[contains(., 'Menu')]")
            if menu_sections:
                menu_sections[0].click()
                time.sleep(2)
        except:
            pass

        # Check for menu items
        try:
            all_text = driver.find_element(By.TAG_NAME, "body").text
            menu_items = extract_menu_items(all_text)
            
            # Try to click on "More" buttons to expand menu sections
            more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'more')]")
            for button in more_buttons[:3]:  # Limit to first 3 "more" buttons to avoid clicking too many
                try:
                    button.click()
                    time.sleep(1)
                    # Get updated text and extract menu items
                    updated_text = driver.find_element(By.TAG_NAME, "body").text
                    menu_items.extend(extract_menu_items(updated_text))
                except:
                    pass
            
            # Remove duplicates based on item name
            menu_dict = {}
            for item in menu_items:
                menu_dict[item["name"]] = item
            menu_items = list(menu_dict.values())
            
        except Exception as e:
            print(f"Error extracting menu items: {str(e)}")
        
        # Try to find menu items in reviews
        try:
            review_sections = driver.find_elements(By.XPATH, "//button[contains(., 'Reviews')]")
            if review_sections:
                review_sections[0].click()
                time.sleep(2)
                
                # Scroll the reviews section to load more
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                
                # Get review text
                reviews_text = " ".join([elem.text for elem in driver.find_elements(By.CSS_SELECTOR, ".wiI7pd")])
                
                # Extract menu items from reviews
                menu_items_from_reviews = extract_menu_items(reviews_text)
                
                # Add non-duplicate items
                existing_names = [item["name"].lower() for item in menu_items]
                for item in menu_items_from_reviews:
                    if item["name"].lower() not in existing_names:
                        menu_items.append(item)
                        existing_names.append(item["name"].lower())
            
        except Exception as e:
            print(f"Error extracting menu items from reviews: {str(e)}")
        
    except Exception as e:
        print(f"Error accessing place: {str(e)}")
    
    print(f"Found {len(menu_items)} menu items")
    return menu_items

def collect_menu_from_website(driver, website_url):
    """
    Collect menu information from a coffee shop's website.
    
    Args:
        driver: Selenium WebDriver
        website_url: The URL of the coffee shop's website
        
    Returns:
        List of menu items with prices
    """
    menu_items = []
    
    if not website_url or not website_url.startswith(('http://', 'https://')):
        return menu_items
    
    try:
        driver.get(website_url)
        time.sleep(3)  # Wait for page to load
        
        print(f"Collecting menu from: {driver.title}")
        
        # Try to find and click menu links
        menu_links = driver.find_elements(By.XPATH, "//a[contains(translate(text(), 'MENU', 'menu'), 'menu') or contains(@href, 'menu')]")
        if menu_links:
            menu_found = False
            for link in menu_links[:1]:  # Try just the first menu link
                try:
                    link.click()
                    time.sleep(2)
                    menu_found = True
                    break
                except:
                    pass
            
            if menu_found:
                # Extract text from the page
                page_text = driver.find_element(By.TAG_NAME, "body").text
                menu_items = extract_menu_items(page_text)
        
        # If no menu links found or no items extracted, try to find menu on the current page
        if not menu_items:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            menu_items = extract_menu_items(page_text)
        
    except Exception as e:
        print(f"Error accessing website: {str(e)}")
    
    print(f"Found {len(menu_items)} menu items")
    return menu_items

def enhance_price_data():
    """
    Enhance the existing coffee shop data with more detailed price information.
    This function loads the existing data, then tries to extract more detailed
    menu and price information from Google Maps and coffee shop websites.
    """
    driver = setup_driver()
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Load existing data
        base_dir = os.path.dirname(os.path.abspath(__file__))
        raw_data_dir = os.path.join(base_dir, PATHS['raw_data'])
        
        # Load Google Maps data
        google_maps_data = []
        google_maps_file = os.path.join(raw_data_dir, "google_maps_latest.json")
        if os.path.exists(google_maps_file):
            try:
                with open(google_maps_file, 'r', encoding='utf-8') as f:
                    google_maps_data = json.load(f)
                    print(f"Loaded {len(google_maps_data)} records from Google Maps data")
            except Exception as e:
                print(f"Error loading Google Maps data: {e}")
        
        # Load Foursquare data
        foursquare_data = []
        foursquare_file = os.path.join(raw_data_dir, "foursquare_latest.json")
        if os.path.exists(foursquare_file):
            try:
                with open(foursquare_file, 'r', encoding='utf-8') as f:
                    foursquare_data = json.load(f)
                    print(f"Loaded {len(foursquare_data)} records from Foursquare data")
            except Exception as e:
                print(f"Error loading Foursquare data: {e}")
        
        # Enhance Google Maps data with menu information
        print("\n=== Enhancing Google Maps data with menu information ===")
        for i, shop in enumerate(google_maps_data):
            if not isinstance(shop, dict) or not shop.get("place_id"):
                continue
            
            print(f"\nProcessing {i+1}/{len(google_maps_data)}: {shop.get('name', 'Unknown')}")
            
            # Skip if we already have menu items
            if shop.get("menu_items") and len(shop.get("menu_items")) > 0:
                print(f"Already have menu items for this shop, skipping...")
                continue
            
            # Add a random delay to avoid rate limiting
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            # Initialize menu_items list if not present
            if "menu_items" not in shop:
                shop["menu_items"] = []
            
            # Collect menu from Google Maps
            if shop.get("place_id"):
                print(f"Collecting menu from Google Maps...")
                menu_items = collect_menu_from_google_maps(driver, shop["place_id"])
                if menu_items:
                    shop["menu_items"].extend(menu_items)
            
            # Collect menu from website if available
            if shop.get("website"):
                print(f"Collecting menu from website: {shop['website']}")
                menu_items = collect_menu_from_website(driver, shop["website"])
                if menu_items:
                    # Add non-duplicate items
                    existing_names = [item["name"].lower() for item in shop["menu_items"]]
                    for item in menu_items:
                        if item["name"].lower() not in existing_names:
                            shop["menu_items"].append(item)
                            existing_names.append(item["name"].lower())
            
            print(f"Total menu items found: {len(shop['menu_items'])}")
            
            # Stop after processing some shops for testing
            if i >= 15:  # Process just 15 shops for now
                print("Processed 15 shops, stopping for now...")
                break
        
        # Enhance Foursquare data with menu information
        print("\n=== Enhancing Foursquare data with menu information ===")
        for i, shop in enumerate(foursquare_data):
            if not isinstance(shop, dict) or not shop.get("place_id"):
                continue
                
            print(f"\nProcessing {i+1}/{len(foursquare_data)}: {shop.get('name', 'Unknown')}")
            
            # Skip if we already have menu items
            if shop.get("menu_items") and len(shop.get("menu_items")) > 0:
                print(f"Already have menu items for this shop, skipping...")
                continue
            
            # Add a random delay to avoid rate limiting
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            # Initialize menu_items list if not present
            if "menu_items" not in shop:
                shop["menu_items"] = []
            
            # Collect menu from Foursquare
            if shop.get("url"):
                print(f"Collecting menu from Foursquare page...")
                # Visit the shop's page and try to find menu items
                try:
                    driver.get(shop["url"])
                    time.sleep(3)
                    
                    # Find menu section if available
                    menu_sections = driver.find_elements(By.XPATH, "//*[contains(text(), 'Menu') or contains(text(), 'menu')]")
                    for section in menu_sections:
                        try:
                            section.click()
                            time.sleep(2)
                            break
                        except:
                            pass
                    
                    # Extract text and look for menu items
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    menu_items = extract_menu_items(page_text)
                    
                    if menu_items:
                        shop["menu_items"].extend(menu_items)
                except Exception as e:
                    print(f"Error collecting from Foursquare page: {str(e)}")
            
            # Collect menu from website if available
            if shop.get("website"):
                print(f"Collecting menu from website: {shop['website']}")
                menu_items = collect_menu_from_website(driver, shop["website"])
                if menu_items:
                    # Add non-duplicate items
                    existing_names = [item["name"].lower() for item in shop["menu_items"]]
                    for item in menu_items:
                        if item["name"].lower() not in existing_names:
                            shop["menu_items"].append(item)
                            existing_names.append(item["name"].lower())
            
            print(f"Total menu items found: {len(shop['menu_items'])}")
            
            # Stop after processing some shops for testing
            if i >= 15:  # Process just 15 shops for now
                print("Processed 15 shops, stopping for now...")
                break
        
        # Save enhanced data
        print("\n=== Saving enhanced data ===")
        # Google Maps
        enhanced_google_maps_file = os.path.join(raw_data_dir, f"google_maps_enhanced_{timestamp}.json")
        with open(enhanced_google_maps_file, 'w', encoding='utf-8') as f:
            json.dump(google_maps_data, f, ensure_ascii=False, indent=4)
        
        # Also update the latest file
        with open(google_maps_file, 'w', encoding='utf-8') as f:
            json.dump(google_maps_data, f, ensure_ascii=False, indent=4)
        
        # Foursquare
        enhanced_foursquare_file = os.path.join(raw_data_dir, f"foursquare_enhanced_{timestamp}.json")
        with open(enhanced_foursquare_file, 'w', encoding='utf-8') as f:
            json.dump(foursquare_data, f, ensure_ascii=False, indent=4)
        
        # Also update the latest file
        with open(foursquare_file, 'w', encoding='utf-8') as f:
            json.dump(foursquare_data, f, ensure_ascii=False, indent=4)
        
        print("\n=== Enhancement complete! ===")
        print(f"Enhanced Google Maps data saved to: {enhanced_google_maps_file}")
        print(f"Enhanced Foursquare data saved to: {enhanced_foursquare_file}")
        
    except Exception as e:
        print(f"Error during enhancement: {e}")
    
    finally:
        # Always close the driver
        print("Closing WebDriver...")
        driver.quit()

if __name__ == "__main__":
    print("Starting coffee shop menu price enhancement...")
    enhance_price_data()
