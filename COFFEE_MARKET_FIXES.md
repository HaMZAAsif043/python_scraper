# Coffee Market Data Collector Improvements

## Overview of Changes

This document explains the improvements made to the Coffee Market Data Collector script to fix two major issues:

1. **Daraz Price Extraction and Pagination**
   - Fixed price extraction logic to properly extract prices from various selectors
   - Implemented full pagination support to extract all 102 pages of products

2. **Alfatah Infinite Scrolling**
   - Implemented support for infinite scrolling instead of pagination
   - Added tracking of already processed products to avoid duplicates

## Improvements in Detail

### 1. Daraz Price Extraction and Pagination

The original implementation had two issues:
- It couldn't reliably extract prices due to inconsistent HTML structure on Daraz
- It was limited to only 10 pages of results instead of the full 102 pages

#### Changes Made:

1. **Price Extraction Improvements**:
   - Added multiple price selectors to handle different product card layouts
   - Added data attribute extraction (`data-price`) which often contains the raw price
   - Improved the price text cleaning with more robust regex patterns
   - Added error handling and debug logging for price extraction

2. **Pagination Enhancement**:
   - Increased the default `max_pages` parameter to 102
   - Added page number tracking in logs (e.g., "Processing page 5/102")
   - Added random delays between page requests to avoid rate limiting
   - Improved error handling and debugging for pagination

### 2. Alfatah Infinite Scrolling Implementation

The original implementation used pagination for Alfatah, but the website actually uses infinite scrolling, where more products are loaded as the user scrolls down the page.

#### Changes Made:

1. **New Method `extract_alfatah_data_with_infinite_scroll`**:
   - Uses Selenium to simulate scrolling behavior
   - Scrolls to the bottom of the page multiple times to trigger content loading
   - Waits for new content to load after each scroll
   - Checks if page height changed to determine if more content was loaded

2. **Product Tracking**:
   - Implemented a unique product ID generation based on product attributes
   - Maintains a set of already processed product IDs to avoid duplicates
   - Only processes new products in each scroll iteration

3. **Performance and Reliability**:
   - Added error handling and recovery
   - Implemented proper cleanup of Selenium resources
   - Added detailed logging for monitoring and debugging

## How to Test the Improvements

A test script (`test_coffee_fixes.py`) has been provided to verify the fixes:

1. **Testing Daraz Price Extraction**:
   - Extracts products from Daraz with the improved method
   - Verifies that prices are extracted correctly (non-zero values)
   - Calculates and reports the price extraction success rate

2. **Testing Alfatah Infinite Scrolling**:
   - Runs the new infinite scrolling implementation
   - Verifies that products are successfully extracted

## Running the Tests

To run the tests and verify the fixes:

```bash
python test_coffee_fixes.py
```

## Applying the Fixes

The fixes have been applied by running:

```bash
python apply_fixes.py
```

This script:
1. Created a backup of the original file
2. Applied the improved Daraz method
3. Added the new Alfatah infinite scrolling method
4. Updated the `collect_data` method to use the new Alfatah method

## Original vs. New Implementation

### Original Daraz Price Extraction:
```python
price_selector = self.target_websites['daraz']['price_selector']
price_elem = card.select_one(price_selector) or card.select_one('.price') or card.select_one('[data-price]')
price_text = price_elem.text.strip() if price_elem else "0"
price_text = price_text.replace("Rs.", "").replace(",", "").replace("PKR", "").strip()

try:
    product_data['price'] = float(price_text)
except ValueError:
    product_data['price'] = 0
```

### New Daraz Price Extraction:
```python
price_elem = None
price_selectors = [
    '.price--NVB62',
    '.currency--GVKjl',
    'span[data-price]',
    'div.price', 
    '.pdp-price',
    '.product-price',
    '[data-qa-locator="product-price"]'
]

for selector in price_selectors:
    price_elem = card.select_one(selector)
    if price_elem:
        break

if price_elem and price_elem.has_attr('data-price'):
    # Get price from data attribute if available
    try:
        product_data['price'] = float(price_elem['data-price'])
    except (ValueError, TypeError):
        product_data['price'] = 0
else:
    # Extract from text content
    price_text = price_elem.text.strip() if price_elem else "0"
    
    # Clean price text thoroughly
    price_text = re.sub(r'[^\d.]', '', price_text.replace(',', '').replace('Rs.', '').replace('PKR', ''))
    
    try:
        product_data['price'] = float(price_text) if price_text else 0
    except ValueError:
        product_data['price'] = 0
```

### Original Alfatah Implementation:
Used standard pagination which didn't work properly with infinite scrolling sites.

### New Alfatah Infinite Scrolling Implementation:
Fully implemented in the new `extract_alfatah_data_with_infinite_scroll` method.
