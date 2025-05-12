# Foodpanda Coffee Product Data Extraction

This script extracts coffee product data from a Foodpanda HTML file and saves it as a structured JSON file. 
It parses the HTML content, identifies coffee products, and extracts relevant product information.

## Features

- Extracts product name, price, image URL, and product URL
- Identifies and extracts product brand
- Categorizes products by coffee type (instant, ground, beans, capsules, mix)
- Extracts packaging information (size and unit)
- Categorizes products by price tier
- Command-line interface for easy usage
- Outputs structured JSON data

## Usage

```bash
python extract_foodpanda_data.py -i [input_html_file] -o [output_json_file]
```

## Example

```bash
python extract_foodpanda_data.py -i foodpanda_debug.html -o coffee_products.json
```

## Requirements

- Python 3.6 or higher
- BeautifulSoup4 (`pip install beautifulsoup4`)

## Output Format

The script generates a JSON file with structured data for each coffee product:

```json
{
  "id": "8288659",
  "scraped_at": "2023-05-12T10:15:20.123456",
  "name": "Nestle Nescafe Classic Coffee Jar 50g",
  "price": 1100.0,
  "image_url": "https://images.deliveryhero.io/image/darkstores/...",
  "product_url": "https://www.foodpanda.pk/darkstore/...",
  "source": "foodpanda.pk",
  "brand": "Nescafe",
  "type": "instant",
  "packaging": {
    "value": 50.0,
    "unit": "g",
    "display": "50.0g"
  },
  "price_tier": "medium"
}
```

## Known Limitations

- Currently only processes a single HTML file, not handling pagination
- Limited to the data available in the product cards
- May need adjustments if Foodpanda updates their HTML structure
