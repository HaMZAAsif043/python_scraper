import asyncio
from playwright.async_api import async_playwright
import json
import requests
import os
import time
from datetime import datetime

# List of cities for testing (using a smaller subset first)
test_cities = [
    "Karachi", "Lahore", "Islamabad", "Rawalpindi"
]

async def discover_pandamart_vendors(cities):
    """
    Discover Pandamart vendor IDs across different cities in Pakistan using Playwright
    """
    vendor_ids = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for production
        page = await browser.new_page()
        
        try:
            await page.goto("https://www.foodpanda.pk/")
            
            for city in cities:
                try:
                    print(f"\n🔍 Searching for Pandamart in {city}...")
                    
                    # Navigate and select location
                    try:
                        await page.click('text=Change location', timeout=5000)
                    except:
                        # If "Change location" is not found, try alternate methods
                        try:
                            await page.click('[data-testid="location-panel-change-location"]', timeout=3000)
                        except:
                            await page.click('button:has-text("Change")', timeout=3000)
                    
                    # Enter city name
                    await page.fill('input[placeholder="Enter your delivery address"]', city)
                    await page.wait_for_timeout(2000)
                    
                    # Click first suggestion
                    await page.keyboard.press("ArrowDown")
                    await page.keyboard.press("Enter")
                    await page.wait_for_load_state("networkidle")
                    
                    # Search for Pandamart
                    search_box = await page.query_selector('input[type="search"]')
                    if search_box:
                        await search_box.fill("pandamart")
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(3000)
                    else:
                        print(f"⚠️ No search box found in {city}")
                        continue
                    
                    # Find Pandamart vendor
                    links = await page.locator('a:has-text("pandamart")').all()
                    if links:
                        url = await links[0].get_attribute("href")
                        if url:
                            # Extract vendor ID from URL (like /sx92/pandamart)
                            parts = url.split("/")
                            vendor_id = parts[2] if len(parts) > 2 else "Not found"
                            vendor_ids[city] = vendor_id
                            print(f"✅ {city}: {vendor_id}")
                        else:
                            print(f"⚠️ No href found for Pandamart in {city}")
                    else:
                        print(f"❌ No Pandamart found in {city}")
                
                except Exception as e:
                    print(f"❌ Error in {city}: {str(e)}")
            
        finally:
            await browser.close()
    
    return vendor_ids

def fetch_coffee_products_via_graphql(vendor_id, city):
    """
    Fetch coffee products from a Pandamart vendor using the Foodpanda GraphQL API
    """
    print(f"\n📡 Fetching coffee products from {city} (vendor: {vendor_id})...")
    
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
            print(f"✅ Found {len(products)} coffee products in {city}")
            return {
                "city": city,
                "vendor_id": vendor_id,
                "products": products
            }
        else:
            print(f"❌ No products found or error in response for {city}")
            return None
            
    except Exception as e:
        print(f"❌ API request error for {city}: {str(e)}")
        return None

async def main():
    # Step 1: Discover Pandamart vendors across cities
    print("🚀 Starting Pandamart vendor discovery...")
    vendor_ids = await discover_pandamart_vendors(test_cities)
    
    # Step 2: Fetch coffee products for each vendor
    all_coffee_data = []
    
    print("\n🔍 Fetching coffee products from each vendor...")
    for city, vendor_id in vendor_ids.items():
        coffee_data = fetch_coffee_products_via_graphql(vendor_id, city)
        if coffee_data:
            all_coffee_data.append(coffee_data)
        # Wait between requests to avoid rate limiting
        time.sleep(2)
    
    # Step 3: Save the results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"foodpanda_coffee_products_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_coffee_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Data saved to {output_file}")
    print(f"📊 Total cities with data: {len(all_coffee_data)}")
    total_products = sum(len(data["products"]) for data in all_coffee_data)
    print(f"📊 Total coffee products: {total_products}")

if __name__ == "__main__":
    # Ensure the output directory exists
    os.makedirs("data/raw", exist_ok=True)
    
    # Run the main function
    asyncio.run(main())
