# Coffee Shop Data Analysis System

A comprehensive system for collecting, analyzing, and visualizing data about coffee shops in Pakistan using free resources and APIs.

## Overview

This project provides tools to analyze the coffee shop market in Pakistan by collecting data from various sources including:

- Coffee shop listings from Google Maps (using web scraping)
- Social media mentions and trends (simulated data)
- Menu prices from food delivery apps (web scraping and simulated data)
- Market trends and competitor intelligence (public data sources)

All data is collected using **FREE** methods without relying on paid APIs.

## Features

- **Data Collection**: Get coffee shop data from multiple sources without paid APIs
- **Data Analysis**: Statistical analysis of pricing, ratings, and market trends
- **Visualization**: Generate interactive dashboards and charts
- **Forecasting**: Predict price trends and market shifts
- **Competitive Analysis**: Compare market share and pricing strategies

## Installation

1. Clone this repository
2. Install dependencies:

```
pip install -r requirements.txt
```

## Usage

### Run the Full Pipeline

```powershell
cd "c:\path\to\python automation"
python src\main.py full
```

### Run Individual Components

```powershell
# Collect data only
python src\main.py collect

# Process data
python src\main.py process

# Run analysis
python src\main.py analyze

# Generate visualizations
python src\main.py visualize
```

### Run on a Schedule

The system can automatically run data collection and analysis on a schedule:

```powershell
python src\main.py
```

This will run the full pipeline immediately and then schedule it to run weekly.

## Demo Notebook

Explore a demo Jupyter notebook to see the system in action:

```powershell
jupyter notebook notebooks\coffee_shop_analysis_demo.ipynb
```

## Project Structure

- `data/` - Raw and processed data storage
- `notebooks/` - Jupyter notebooks for demonstrations and exploration
- `reports/` - Generated reports and visualizations
- `src/` - Source code
  - `config.py` - Configuration settings
  - `main.py` - Main pipeline orchestration
  - `data_collection/` - Modules for collecting data from various sources
  - `data_processing/` - Data cleaning and transformation
  - `data_analysis/` - Statistical analysis and trend detection
  - `visualization/` - Dashboard and report generation

## Free Data Collection Methods

This project uses the following methods to collect data without paid APIs:

1. **Google Maps**: Uses web scraping with Selenium WebDriver to extract coffee shop listings
2. **Social Media**: Generates realistic simulated data based on patterns observed in actual datasets
3. **Food Delivery**: Uses web scraping and data generation to create realistic menu data
4. **Market Trends**: Collects information from public datasets and free resources

## Note

This project is intended for educational purposes. Web scraping may be subject to terms of service for the respective websites. Always ensure you're complying with any applicable terms of service when using web scraping.

## License

MIT