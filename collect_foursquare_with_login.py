import os
import json
import time
import random
import re
import csv
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

# Login credentials
EMAIL = "asifnaseer043@gmail.com"
PASSWORD = "Thyroxin@43"

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    options = Options()
    options.add_argument("--start-maximized")
    # Optional: Hide automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Return the driver
    return webdriver.Chrome(options=options)

def login_to_foursquare(driver):
    """
    Login to Foursquare using the provided credentials.
    
    Args:
        driver: Selenium WebDriver
    
    Returns:
        Boolean indicating success or failure
    """
    try:
        print("Attempting to log in to Foursquare...")
        driver.get("https://foursquare.com/login")
        
        # Wait for login form to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
        )
        
        # Enter email
        email_field = driver.find_element(By.CSS_SELECTOR, "input[name='email']")
        email_field.clear()
        email_field.send_keys(EMAIL)
        time.sleep(1)
        
        # Enter password
        password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        time.sleep(1)
        
        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for successful login (check for avatar or user menu)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".avatar, .userMenu"))
        )
        
        print("Successfully logged in to Foursquare!")
        return True
        
    except Exception as e:
        print(f"Failed to login: {str(e)}")
        # Take a screenshot of the error
        screenshot_path = f"foursquare_login_error_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Error screenshot saved to {screenshot_path}")
        return False

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
    try:
        print("Waiting for search results...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='card-container']"))
        )
    except TimeoutException:
        print(f"Timeout waiting for search results in {location}")
        # Save screenshot for debugging
        screenshot_path = f"foursquare_error_{city.replace(' ', '_')}_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Error screenshot saved to {screenshot_path}")
        return []
    
    # Scroll to load more results
    print(f"Scrolling to load more results ({max_scrolls} scrolls)...")
    for i in range(max_scrolls):
        print(f"Scroll {i+1}/{max_scrolls}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2 + random.random())  # Add random delay
    
    # Find all coffee shop cards
    coffee_shops = []
    try:
        shop_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='card-container']")
        print(f"Found {len(shop_cards)} coffee shop cards")
        
        for i, card in enumerate(shop_cards):
            try:
                # Extract shop data
                shop_data = {}
                
                # Get shop name
                try:
                    name_element = card.find_element(By.CSS_SELECTOR, "h2")
                    shop_data["name"] = name_element.text.strip()
                except:
                    continue  # Skip entries without name
                
                # Get shop URL
                try:
                    link_element = card.find_element(By.CSS_SELECTOR, "a[data-testid='card-container-link']")
                    shop_url = link_element.get_attribute("href")
                    shop_data["url"] = shop_url
                    # Extract venue ID from URL
                    venue_id_match = re.search(r'/v/([^/]+)', shop_url)
                    if venue_id_match:
                        shop_data["place_id"] = venue_id_match.group(1)
                    else:
                        shop_data["place_id"] = f"fs-{i}-{int(time.time())}"
                except:
                    shop_data["place_id"] = f"fs-{i}-{int(time.time())}"
                    shop_data["url"] = ""
                
                # Get rating if available
                try:
                    rating_element = card.find_element(By.CSS_SELECTOR, "span[data-testid='rating-score']")
                    shop_data["rating"] = float(rating_element.text.strip())
                except:
                    shop_data["rating"] = None
                
                # Get number of ratings if available
                try:
                    review_count_element = card.find_element(By.CSS_SELECTOR, "span[data-testid='rating-count']")
                    count_text = review_count_element.text.strip()
                    count_match = re.search(r'(\d+)', count_text)
                    if count_match:
                        shop_data["user_ratings_total"] = int(count_match.group(1))
                    else:
                        shop_data["user_ratings_total"] = None
                except:
                    shop_data["user_ratings_total"] = None
                
                # Get price level if available
                try:
                    price_element = card.find_element(By.CSS_SELECTOR, "span[data-testid='priceRange']")
                    price_text = price_element.text.strip()
                    shop_data["price_level"] = len(price_text)  # Count $ symbols
                    shop_data["price_text"] = price_text
                except:
                    shop_data["price_level"] = None
                    shop_data["price_text"] = None
                
                # Get address if available
                try:
                    address_element = card.find_element(By.CSS_SELECTOR, "div[data-testid='card-container-address']")
                    shop_data["address"] = address_element.text.strip()
                except:
                    shop_data["address"] = ""
                
                # Get category/type if available
                try:
                    category_element = card.find_element(By.CSS_SELECTOR, "div[data-testid='card-container-inline-category']")
                    shop_data["category"] = category_element.text.strip()
                except:
                    shop_data["category"] = ""
                
                # Add metadata
                shop_data["location"] = location
                shop_data["data_source"] = "foursquare_scraper"
                shop_data["collected_at"] = datetime.now().isoformat()
                
                print(f"Extracted data for: {shop_data['name']}")
                coffee_shops.append(shop_data)
                
                # Detailed information extraction - visit individual shop pages
                if shop_data["url"] and len(coffee_shops) <= 10:  # Limit to 10 detailed page visits per city
                    try:
                        detailed_data = get_detailed_shop_info(driver, shop_data["url"])
                        shop_data.update(detailed_data)
                    except Exception as e:
                        print(f"Error getting detailed info: {e}")
                
            except Exception as e:
                print(f"Error processing shop card {i}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error extracting coffee shops: {str(e)}")
    
    return coffee_shops

def get_detailed_shop_info(driver, shop_url):
    """
    Visit individual shop page and extract detailed information like prices,
    busy hours, menu items, etc.
    
    Args:
        driver: Selenium WebDriver
        shop_url: URL of the shop's page on Foursquare
        
    Returns:
        Dictionary with detailed shop information
    """
    print(f"Getting detailed information from: {shop_url}")
    detailed_data = {}
    
    # Store current URL to return later
    current_url = driver.current_url
    
    try:
        # Visit the shop's page
        driver.get(shop_url)
        time.sleep(3 + random.random())  # Wait for page to load
        
        # Extract menu items and prices if available
        try:
            menu_items = []
            price_elements = driver.find_elements(By.CSS_SELECTOR, ".venueMenuItem")
            
            for item_element in price_elements:
                try:
                    item_name = item_element.find_element(By.CSS_SELECTOR, ".venueMenuItem-name").text.strip()
                    
                    # Try to find price
                    try:
                        item_price = item_element.find_element(By.CSS_SELECTOR, ".venueMenuItem-price").text.strip()
                    except:
                        item_price = "N/A"
                        
                    # Try to find description
                    try:
                        item_desc = item_element.find_element(By.CSS_SELECTOR, ".venueMenuItem-description").text.strip()
                    except:
                        item_desc = ""
                    
                    menu_items.append({
                        "name": item_name,
                        "price": item_price,
                        "description": item_desc
                    })
                except:
                    continue
            
            if menu_items:
                detailed_data["menu_items"] = menu_items
        except:
            pass
        
        # Extract popular times/busy hours if available
        try:
            popular_times = {}
            popular_time_elements = driver.find_elements(By.CSS_SELECTOR, ".popular-times")
            
            if popular_time_elements:
                for day_element in driver.find_elements(By.CSS_SELECTOR, ".popular-day"):
                    day_name = day_element.find_element(By.CSS_SELECTOR, ".day-name").text.strip()
                    hour_data = []
                    
                    hour_bars = day_element.find_elements(By.CSS_SELECTOR, ".hour-bar")
                    for i, bar in enumerate(hour_bars):
                        # Approximating the hour based on position
                        hour = 8 + i  # Assuming business hours start at 8 AM
                        popularity_style = bar.get_attribute("style")
                        
                        # Extract height percentage which indicates popularity
                        popularity = 0
                        height_match = re.search(r'height:\s*(\d+)%', popularity_style)
                        if height_match:
                            popularity = int(height_match.group(1))
                        
                        hour_data.append({
                            "hour": hour,
                            "popularity": popularity
                        })
                    
                    popular_times[day_name] = hour_data
                
                if popular_times:
                    detailed_data["popular_times"] = popular_times
        except:
            pass
        
        # Extract contact information
        try:
            contact_info = {}
            
            # Phone number
            try:
                phone_element = driver.find_element(By.XPATH, "//a[contains(@href, 'tel:')]")
                contact_info["phone"] = phone_element.text.strip()
            except:
                pass
                
            # Website
            try:
                website_element = driver.find_element(By.XPATH, "//a[contains(@href, 'http') and @target='_blank']")
                contact_info["website"] = website_element.get_attribute("href")
            except:
                pass
            
            if contact_info:
                detailed_data.update(contact_info)
        except:
            pass
        
    except Exception as e:
        print(f"Error during detailed info extraction: {e}")
    finally:
        # Return to the search results page
        driver.get(current_url)
        time.sleep(1)
    
    return detailed_data

def collect_and_save_data():
    """Collect coffee shop data from Foursquare and save to JSON and CSV files."""
    driver = setup_driver()
    all_coffee_shops = []
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # First login to Foursquare
        login_success = login_to_foursquare(driver)
        if not login_success:
            print("Proceeding without login...")
        
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
        json_file = os.path.join(output_dir, f"foursquare_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
        
        # Also save a 'latest' copy for easy access
        latest_json_file = os.path.join(output_dir, "foursquare_latest.json")
        with open(latest_json_file, 'w', encoding='utf-8') as f:
            json.dump(all_coffee_shops, f, ensure_ascii=False, indent=4)
        
        # Save data to CSV file
        csv_file = os.path.join(output_dir, f"foursquare_{timestamp}.csv")
        save_data_to_csv(all_coffee_shops, csv_file)
        
        # Also save a 'latest' copy of CSV
        latest_csv_file = os.path.join(output_dir, "foursquare_latest.csv")
        save_data_to_csv(all_coffee_shops, latest_csv_file)
        
        print(f"\n=== Collection complete! ===")
        print(f"Collected data for {len(all_coffee_shops)} coffee shops")
        print(f"Data saved to: {json_file}")
        print(f"CSV file saved to: {csv_file}")
        
        return all_coffee_shops
    
    except Exception as e:
        print(f"Error during data collection: {e}")
        return []
    
    finally:
        # Always close the driver
        print("Closing WebDriver...")
        driver.quit()

def save_data_to_csv(coffee_shops, csv_file):
    """
    Save coffee shop data to a CSV file.
    
    Args:
        coffee_shops: List of coffee shop dictionaries
        csv_file: Output CSV file path
    """
    if not coffee_shops:
        print("No data to save to CSV.")
        return
    
    # Define columns for the CSV file
    columns = [
        "name", "location", "address", "rating", "user_ratings_total", 
        "price_level", "price_text", "category", "phone", "website", 
        "place_id", "url", "data_source", "collected_at"
    ]
    
    # Add columns for menu items and prices
    menu_columns = []
    for shop in coffee_shops:
        if "menu_items" in shop:
            for item in shop["menu_items"]:
                col_name = f"menu_item_{item['name']}_price"
                if col_name not in menu_columns:
                    menu_columns.append(col_name)
    
    all_columns = columns + menu_columns
    
    # Write to CSV
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns)
            writer.writeheader()
            
            for shop in coffee_shops:
                # Create a flat dictionary for CSV row
                flat_shop = {key: shop.get(key, "") for key in columns}
                
                # Add menu items and prices
                if "menu_items" in shop:
                    for item in shop["menu_items"]:
                        col_name = f"menu_item_{item['name']}_price"
                        if col_name in menu_columns:
                            flat_shop[col_name] = item['price']
                
                writer.writerow(flat_shop)
        
        print(f"CSV file saved successfully: {csv_file}")
    except Exception as e:
        print(f"Error saving CSV file: {e}")

if __name__ == "__main__":
    print("Starting coffee shop data collection from Foursquare...")
    collect_and_save_data()
