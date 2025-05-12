# Coffee Shop Data Analysis System

This system collects, processes, and analyzes coffee shop data from various sources to generate business insights for coffee shop operators in Pakistan.

## System Components

1. **Data Collection**:
   - Google Maps web scraping (`collect_data.py`)
   - Foursquare web scraping with login capabilities (`collect_foursquare_with_login.py`)
   - Menu price information collection (`collect_menu_prices.py`)

2. **Data Processing**:
   - Convert to CSV with focused data on prices and traffic (`convert_to_csv.py`)
   - Generate Excel reports with price comparisons

3. **Data Analysis**:
   - Statistical analysis (`src/data_analysis/statistical_analysis.py`)
   - Trend analysis (`src/data_analysis/trend_analysis.py`)

4. **Visualization**:
   - Interactive dashboard (`src/visualization/dashboard.py`)
   - Price comparison charts (`visualize_prices.py`)

## Getting Started

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

### Usage

1. **Collect data** from Google Maps:
   ```
   python collect_data.py
   ```

2. **Collect data** from Foursquare (with login):
   ```
   python collect_foursquare_with_login.py
   ```

3. **Convert data** to CSV format:
   ```
   python convert_to_csv.py
   ```

4. **Enhance menu price data**:
   ```
   python collect_menu_prices.py
   ```

5. **Generate price visualizations**:
   ```
   python visualize_prices.py
   ```

6. **Run the full pipeline**:
   ```
   python src/main.py
   ```

7. **Generate visualizations only**:
   ```
   python src/main.py visualize
   ```

## Data Files

The system generates the following data files:

### Raw Data
- `data/raw/google_maps_latest.json`: Latest Google Maps data
- `data/raw/foursquare_latest.json`: Latest Foursquare data

### Processed Data
- `data/processed/coffee_shops_basic_latest.csv`: General information about coffee shops
- `data/processed/coffee_shops_prices_latest.csv`: Detailed price information
- `data/processed/coffee_shops_traffic_latest.csv`: Traffic patterns and busy hours
- `data/processed/coffee_price_comparison_latest.xlsx`: Excel report with price comparisons

### Reports
- `reports/price_distribution_latest.png`: Distribution of coffee prices
- `reports/price_by_city_latest.png`: Comparison of coffee prices by city
- `reports/price_by_coffee_type_latest.png`: Comparison of prices by coffee type
- `reports/price_heatmap_latest.png`: Heatmap showing coffee prices by city and type

## Key Features

1. **Scraping Without API Keys**: Uses Selenium to scrape data without requiring expensive API keys
2. **Price Analysis**: Compares coffee prices across cities and shops
3. **Menu Item Collection**: Extracts specific menu items and their prices
4. **Traffic Analysis**: Analyzes busy hours and traffic patterns
5. **City Comparison**: Compares coffee shop metrics across Pakistani cities
6. **Price Visualization**: Generate price comparison charts by city and coffee type
7. **Visualization**: Generate charts and reports for business intelligence

## Target Locations

The system collects data for these cities in Pakistan:
- Karachi
- Lahore
- Islamabad
- Rawalpindi
- Peshawar
- Multan
- Faisalabad

## Maintenance

If you receive "Element not found" errors or other scraping issues, the websites might have changed their HTML structure. In this case, you may need to update the CSS selectors in the collection scripts.

## Troubleshooting

1. **CAPTCHA Issues**: If you see CAPTCHA challenges during scraping, the script will save screenshots. You may need to manually solve them or use another IP address.
2. **Login Failures**: If Foursquare login fails, check if the credentials are still valid or if Foursquare has changed its login page structure.
3. **No Price Data**: For accurate price data, try increasing the number of detailed page visits in the Foursquare script by adjusting the `len(coffee_shops) <= 10` limit.

## Email for Support

For issues or questions, contact: asifnaseer043@gmail.com
