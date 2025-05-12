# Getting Started with the Coffee Shop Analysis System

This guide will help you get started with the Coffee Shop Data Analysis System.

## Installation

Make sure you have Python 3.8+ installed on your system, then follow these steps:

1. Clone or download this repository to your local machine
2. Open a terminal or command prompt and navigate to the project folder
3. Install the required dependencies:

```
pip install -r requirements.txt
```

## Basic Usage

The system is designed to be modular, allowing you to use each component separately or run the full pipeline.

### Quickstart

To run the full pipeline (collection, processing, analysis, and visualization) once:

```
python src/main.py full
```

### Running Individual Components

You can also run each step of the pipeline separately:

- **Data Collection**: `python src/main.py collect`
- **Data Processing**: `python src/main.py process`
- **Data Analysis**: `python src/main.py analyze`
- **Visualization**: `python src/main.py visualize`

### Scheduled Data Collection

To set up automatic scheduled data collection (runs immediately and then weekly):

```
python src/main.py
```

## Exploring the Data with Jupyter Notebooks

For data exploration and interactive analysis, use the provided Jupyter notebook:

```
jupyter notebook notebooks/coffee_shop_analysis_demo.ipynb
```

This notebook demonstrates how to:
- Collect data from various free sources
- Process and analyze the data
- Create visualizations
- Generate insights

## Free Data Collection Methods

This system uses several free methods to collect coffee shop data:

1. **Web scraping** for Google Maps and food delivery platforms
2. **Simulated data** based on real-world patterns when APIs are paid
3. **Public datasets** for market trends
4. **Social media simulation** to generate realistic trends

## Generated Visualizations

The system creates several visualizations:

1. Coffee shop distribution by city
2. Rating distributions
3. Price trend forecasts
4. Social media hashtag analysis
5. Competitor market share analysis

All visualizations are saved in the `data/processed/visualizations_latest` directory.

## Next Steps

After setting up the system, you can:

1. Customize the target locations in `src/config.py`
2. Modify the data collection modules to fit your specific needs
3. Add new visualization types to the dashboard
4. Create custom reports for your business needs

## Troubleshooting

If you encounter any issues:

1. Check that all dependencies are installed correctly
2. Make sure you have internet access for web scraping
3. Verify the directory structure exists (data/raw, data/processed, reports)
4. Check the log file `coffee_data_system.log` for detailed error messages
