from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Setup WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# Optional: Hide automation flags
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)

# Go to Google Maps
driver.get("https://www.google.com/maps")
time.sleep(3)

# Search for coffee shops
search_input = driver.find_element(By.ID, "searchboxinput")
search_input.send_keys("coffee shops in Lahore")
search_input.send_keys(Keys.ENTER)

# Wait for results to load
time.sleep(10)

# Scroll the results panel to load more
try:
    scrollable = driver.find_element(By.XPATH, '//div[@role="feed"]')
    for _ in range(5):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
        time.sleep(2)
except:
    print("Could not find scrollable div.")

# Find all <a> tags with class 'hfpxzc'
places = driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')

# Extract and print names + links
for place in places:
    name = place.get_attribute('aria-label')
    link = place.get_attribute('href')
    if name and link:
        print(f"{name} — {link}")

driver.quit()
