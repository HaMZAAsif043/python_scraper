# Coffee Market Data Collection

This document explains how to use the Coffee Market Data Collection module to gather information about coffee products sold in Pakistan.

## Overview

The Coffee Market Data Collection module scrapes publicly available data from popular Pakistani e-commerce websites to gather comprehensive information about coffee products available in the market. This data is valuable for market research, competitive analysis, and product positioning for anyone looking to launch or expand a coffee business in Pakistan.

## Data Collected

The module collects the following information about coffee products:

- **Product Names**: Full product names as displayed on websites
- **Brands**: Coffee brand names (Nescafe, Lavazza, etc.)
- **Prices**: Current retail prices in PKR
- **Coffee Types**: Categories like instant, ground, beans, powdered
- **Packaging Information**: Size variants (250g, 500g, 1kg, etc.)
- **Price Tiers**: Categorized as economy, mid-range, or premium
- **Customer Ratings**: Star ratings (when available)
- **Review Counts**: Number of reviews (when available)
- **Source Website**: Which website the data came from

## Data Sources

The module collects data from the following Pakistani e-commerce websites:

- Daraz.pk - Pakistan's largest e-commerce platform
- Alfatah.com.pk - Popular grocery retailer
- Naheed.pk - Major retail chain with extensive grocery section
- Additional sources can be easily added

## Usage

### Running as a standalone script

You can collect coffee market data by running the dedicated script:

```bash
python collect_coffee_market.py
```

This will:
1. Scrape coffee product data from all configured websites
2. Process and categorize the data
3. Save the results in both JSON and CSV formats
4. Display a summary of the collected data

### Integrating with the main data pipeline

The coffee market data collection is also integrated into the main data pipeline. To run it as part of the complete system:

```bash
python src/main.py full
```

Or to run just the collection step:

```bash
python src/main.py collect
```

### Output Files

The script generates several output files:

1. **Raw JSON** - Contains all collected product data in its original form
   - `data/raw/coffee_market_[TIMESTAMP].json`

2. **Processed JSON** - Contains aggregated and categorized data
   - `data/raw/coffee_market_processed_[TIMESTAMP].json`

3. **CSV Files** - For easy import into analysis tools
   - `data/processed/coffee_products_[TIMESTAMP].csv` - All product details
   - `data/processed/coffee_brands_[TIMESTAMP].csv` - Brand statistics
   - `data/processed/coffee_types_[TIMESTAMP].csv` - Coffee type statistics
   - `data/processed/coffee_packaging_[TIMESTAMP].csv` - Packaging statistics

Additionally, "latest" versions of all files are maintained for easy access:
   - `data/processed/coffee_products_latest.csv`
   - `data/processed/coffee_brands_latest.csv`
   - etc.

## Market Research Value

The collected data can be used for:

- **Market Positioning** - Identify gaps in the market by price point, packaging, or coffee type
- **Competitive Analysis** - See which brands dominate which market segments
- **Product Development** - Determine popular packaging sizes and product formats
- **Pricing Strategy** - Understand the price distribution across different tiers
- **Brand Analysis** - Evaluate which brands have the best ratings and largest presence

## Example Analysis Questions

The collected data can help answer questions such as:

- What is the average price of ground coffee vs. instant coffee in the Pakistani market?
- Which packaging size has the highest price per gram?
- Which brands are most represented in the premium segment?
- What's the distribution of product types (instant vs. ground vs. beans)?
- Which brands have the highest average customer ratings?

## Extending the Module

You can extend the module to collect data from additional sources by:

1. Add the new website's URL to the `target_websites` dictionary in `CoffeeMarketDataCollector.__init__`
2. Create a new extraction method following the pattern of existing methods (`extract_daraz_data`, etc.)
3. Call your new extraction method from the `collect_data` method
