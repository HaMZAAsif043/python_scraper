# Foodpanda GraphQL Extractor Usage Guide

This guide explains how to use the Foodpanda GraphQL extractor to collect coffee product data from Pandamart vendors across multiple cities in Pakistan.

## Overview

The Foodpanda GraphQL extractor is designed to:
1. Discover Pandamart vendor IDs across multiple cities using Playwright
2. Extract coffee product data using Foodpanda's GraphQL API
3. Transform and categorize the data into a standardized format
4. Integrate with the existing coffee market data collection system

## Prerequisites

- Python 3.7+
- Required Python packages:
  - playwright
  - requests
  - asyncio
  - logging

## Installation

1. Install the required packages:
   ```bash
   pip install playwright requests
   ```

2. Install the Playwright browser:
   ```bash
   playwright install chromium
   ```

## Available Scripts

This package includes several scripts:

1. **foodpanda_graphql_extractor.py**: Core extraction functionality
2. **foodpanda_graphql_integration.py**: Integration with the main coffee market collector
3. **test_foodpanda_graphql_extraction.py**: Standalone test script
4. **integrate_graphql_extractor.py**: Integration script for coffee_market.py
5. **test_pandamart_graphql.py**: Initial test script for vendor discovery and GraphQL API

## Usage Examples

### 1. Standalone Extraction

To run the extractor as a standalone tool:

```bash
python test_foodpanda_graphql_extraction.py --cities 5 --headless
```

Options:
- `--cities`: Maximum number of cities to process (default: 5)
- `--headless`: Run in headless mode (no browser UI)
- `--show-browser`: Show browser UI during extraction (default behavior)
- `--output`: Custom output file path (optional)

### 2. Integration with Coffee Market Collector

To integrate the extractor with your existing coffee market data collector:

```bash
python integrate_graphql_extractor.py
```

This will:
1. Create a backup of your coffee_market.py file
2. Add the GraphQL extraction method
3. Update the collect_data method to use GraphQL for Foodpanda

After integration, the collector will automatically use the GraphQL extractor when processing Foodpanda data.

### 3. Using the Integration Module Directly

You can also use the integration module in your own scripts:

```python
from foodpanda_graphql_integration import get_graphql_products_for_coffee_market

# Get coffee products
products = get_graphql_products_for_coffee_market()

# Process the products
for product in products:
    print(f"{product['name']} - {product['price']} - {product['brand']}")
```

## Data Format

The extractor returns data in the following format:

```json
[
  {
    "id": "product-id",
    "name": "Product Name",
    "scraped_at": "2023-05-12T10:15:20.123456",
    "price": 1234.56,
    "image_url": "https://example.com/image.jpg",
    "product_url": "https://www.foodpanda.pk/vendor/product",
    "source": "foodpanda.pk (City)",
    "city": "City Name",
    "description": "Product description",
    "brand": "Brand Name",
    "type": "instant",
    "packaging": {
      "value": 200,
      "unit": "g",
      "display": "200g"
    },
    "price_tier": "mid-range"
  }
]
```

### Product Types
- instant
- ground
- beans
- capsule/pod
- coffee mix
- other

### Price Tiers
- economy
- mid-range
- premium

## Caching

The extractor implements caching to improve performance and reduce API load:

- Vendor IDs are cached to avoid re-discovery across runs
- Product data is cached to minimize redundant API calls
- Cache duration is configurable (default: 24 hours)

## Customization

### Modifying City List

Edit the `CITIES` list in `foodpanda_graphql_extractor.py` to add or remove cities:

```python
CITIES = [
    "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
    # Add more cities here
]
```

### Adjusting Cache Duration

Modify the `cache_duration_hours` parameter when initializing the extractor:

```python
extractor = FoodpandaGraphQLExtractor(cache_duration_hours=48)  # 48-hour cache
```

## Troubleshooting

### Common Issues

1. **No Pandamart vendors found**
   - Check internet connection
   - Verify that Foodpanda operates in the target cities
   - Try running without headless mode to observe the browser behavior

2. **GraphQL API errors**
   - Foodpanda may have changed their API structure
   - Check for rate limiting (add delays between requests)
   - Inspect browser network traffic for updated query format

3. **No coffee products returned**
   - Try different search terms ("coffee", "nescafe", etc.)
   - Check the product categorization logic
   - Ensure Pandamart stocks coffee products in the target area

### Logs

The extractor creates log files that can help diagnose issues:
- `foodpanda_graphql.log`: Integration module logs
- `foodpanda_graphql_test.log`: Test script logs

## Advanced Usage

### Custom Product Filtering

The extractor currently filters for coffee products based on name. You can modify the `_is_coffee_product` method in `foodpanda_graphql_extractor.py` to adjust filtering criteria.

### Adding New Product Categories

To add new product categories, modify the `_extract_coffee_type` method in `foodpanda_graphql_extractor.py`.
