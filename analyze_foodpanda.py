#!/usr/bin/env python
"""Script to analyze the Foodpanda website structure"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Set up Chrome options
options = Options()
options.add_argument('--headless')
options.add_argument('--window-size=1920,1080')

# Initialize the driver
driver = webdriver.Chrome(options=options)

try:
    # Navigate to the coffee search page on Foodpanda
    driver.get('https://www.foodpanda.pk/groceries/shop/s/search/coffee')
    
    # Wait for the page to load
    print("Waiting for page to load...")
    time.sleep(10)
    
    # Check for product containers with different selectors
    selectors = [
        '.product-card', 
        '.product-item', 
        '.product',
        '.vendor-product-card',
        '.product-card-vertical',
        '.product-container',
        '.dish-card',
        '.item-card'
    ]
    
    print("Checking HTML structure...")
    for selector in selectors:
        elements = driver.find_elements('css selector', selector)
        print(f"Selector '{selector}': {len(elements)} elements found")
    
    # Save the page source
    with open('foodpanda_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print('Page source saved to foodpanda_page.html')
    
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
    print("Driver closed")
