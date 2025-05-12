#!/usr/bin/env python
"""
Main script for coffee shop data analysis system.
This script orchestrates the entire process of data collection, processing, analysis, and visualization.
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.data_collection.google_maps import collect_google_maps_data
from src.data_collection.social_media import collect_social_media_data
from src.data_collection.food_delivery import collect_food_delivery_data
from src.data_collection.market_trends import collect_market_trends_data
from src.data_collection.coffee_market import collect_coffee_market_data

from src.data_processing.cleaner import clean_data
from src.data_processing.transformer import transform_data

from src.data_analysis.statistical_analysis import perform_statistical_analysis
# from src.data_analysis.trend_analysis import analyze_trends

from src.visualization.dashboard import create_visualizations
# from src.visualization.report_generator import generate_reports

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("coffee_data_system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def full_data_pipeline():
    """Execute the complete data pipeline."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting full data pipeline at {timestamp}")
    try:
        # Step 1: Collect data from various sources
        logger.info("Starting data collection...")
        google_data = collect_google_maps_data()
        social_data = collect_social_media_data()
        delivery_data = collect_food_delivery_data()
        market_data = collect_market_trends_data()
        coffee_market_data = collect_coffee_market_data()
        logger.info("Data collection completed.")
        
        # Step 2: Process and clean the data
        logger.info("Starting data processing...")
        raw_data = {
            'google': google_data,
            'social': social_data,
            'delivery': delivery_data,
            'market': market_data,
            'coffee_market': coffee_market_data
        }
        clean_data(raw_data, timestamp)
        processed_data = transform_data(timestamp)
        logger.info("Data processing completed.")
        
        # Step 3: Analyze the data
        logger.info("Starting data analysis...")
        analysis_results = perform_statistical_analysis(processed_data)
        trend_results = analyze_trends(processed_data)
        logger.info("Data analysis completed.")
        
        # Step 4: Generate visualizations and reports
        logger.info("Generating visualizations and reports...")
        visualization_results = create_visualizations(timestamp=timestamp)
        if visualization_results and 'dashboard' in visualization_results:
            logger.info(f"Dashboard created at {visualization_results['dashboard']}")
        generate_reports(analysis_results, trend_results, timestamp)
        logger.info("Report generation completed.")
        
        logger.info(f"Full data pipeline completed successfully at {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        return True
    
    except Exception as e:
        logger.error(f"Error in data pipeline: {str(e)}")
        return False


def schedule_tasks():
    """Schedule regular data collection and analysis tasks."""
    # Run the full pipeline immediately when the script starts
    full_data_pipeline()
    
    # Schedule the full pipeline to run weekly
    schedule.every().monday.at("01:00").do(full_data_pipeline)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    logger.info("Coffee Shop Data Analysis System starting...")
    
    # If command line arguments are provided, perform specific tasks
    if len(sys.argv) > 1:
        if sys.argv[1] == "collect":
            logger.info("Running data collection only...")
            collect_google_maps_data()
            collect_social_media_data()
            collect_food_delivery_data()
            collect_market_trends_data()
        elif sys.argv[1] == "process":
            timestamp = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info(f"Running data processing only for timestamp {timestamp}...")
            clean_data({}, timestamp)
            transform_data(timestamp)
        elif sys.argv[1] == "analyze":
            timestamp = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info(f"Running analysis only for timestamp {timestamp}...")
            processed_data = {}  # Load processed data
            perform_statistical_analysis(processed_data)
            # analyze_trends(processed_data)
        elif sys.argv[1] == "visualize":
            timestamp = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info(f"Running visualization only for timestamp {timestamp}...")
            visualization_results = create_visualizations(timestamp=timestamp)
            if visualization_results and 'dashboard' in visualization_results:
                logger.info(f"Dashboard created at {visualization_results['dashboard']}")
            # generate_reports({}, {}, timestamp) # Empty dictionaries as placeholders
        elif sys.argv[1] == "full":
            logger.info("Running full pipeline once...")
            full_data_pipeline()
        else:
            logger.info("Unknown command. Starting scheduled tasks...")
            schedule_tasks()
    else:
        # No arguments provided, start scheduled tasks
        schedule_tasks()
