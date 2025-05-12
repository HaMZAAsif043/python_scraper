"""
Module for statistical analysis of coffee shop data.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from ..config import PATHS

logger = logging.getLogger(__name__)

class CoffeeShopAnalyzer:
    """Class to perform statistical analysis on coffee shop data."""
    
    def __init__(self, transformed_dir):
        """
        Initialize the analyzer with the directory containing transformed data.
        
        Args:
            transformed_dir (str): Path to the directory containing transformed data
        """
        self.transformed_dir = transformed_dir
        self.analysis_results = {}
    
    def load_data(self):
        """
        Load all transformed data files for analysis.
        
        Returns:
            dict: Dictionary of loaded dataframes
        """
        logger.info(f"Loading transformed data from {self.transformed_dir}")
        
        data = {}
        
        # Load all CSV files in the transformed directory
        for file in os.listdir(self.transformed_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(self.transformed_dir, file)
                try:
                    # Use the filename without extension as the key
                    key = file.rsplit('.', 1)[0]
                    df = pd.read_csv(file_path)
                    data[key] = df
                    logger.info(f"Loaded {key} with shape {df.shape}")
                except Exception as e:
                    logger.error(f"Error loading {file}: {str(e)}")
        
        return data
    
    def analyze_city_data(self, data):
        """
        Analyze coffee shop data by city.
        
        Args:
            data (dict): Dictionary of dataframes
            
        Returns:
            dict: Analysis results for cities
        """
        logger.info("Analyzing coffee shop data by city")
        
        city_results = {}
        
        # Analyze Google Maps city metrics if available
        if 'google_maps_city_metrics' in data:
            df = data['google_maps_city_metrics']
            
            if not df.empty:
                city_results['google_maps'] = {
                    'shop_count_by_city': df[['city', 'coffee_shop_count']].to_dict('records'),
                    'avg_rating_by_city': df[['city', 'rating_mean']].to_dict('records'),
                    'summary': df.describe().to_dict()
                }
                
                # Correlations between metrics
                if all(col in df.columns for col in ['coffee_shop_count', 'rating_mean', 'user_ratings_total_sum']):
                    correlation = df[['coffee_shop_count', 'rating_mean', 'user_ratings_total_sum']].corr()
                    city_results['google_maps']['correlation'] = correlation.to_dict()
        
        # Analyze food delivery metrics by city if available
        if 'food_delivery_metrics_by_city' in data:
            df = data['food_delivery_metrics_by_city']
            
            if not df.empty:
                city_results['food_delivery'] = {
                    'shop_count_by_city': df[['city', 'shop_count']].to_dict('records'),
                    'avg_rating_by_city': df[['city', 'rating_mean']].to_dict('records'),
                    'summary': df.describe().to_dict()
                }
        
        # Analyze Twitter metrics by city if available
        if 'twitter_metrics_by_city' in data:
            df = data['twitter_metrics_by_city']
            
            if not df.empty:
                city_results['twitter'] = {
                    'tweet_count_by_city': df[['city', 'tweet_count']].to_dict('records'),
                    'engagement_by_city': df[['city', 'like_count_sum', 'retweet_count_sum']].to_dict('records'),
                    'summary': df.describe().to_dict()
                }
        
        # Merge datasets for cross-source analysis if all three are available
        if all(k in data for k in ['google_maps_city_metrics', 'food_delivery_metrics_by_city', 'twitter_metrics_by_city']):
            # Prepare dataframes for merger
            gm_df = data['google_maps_city_metrics'][['city', 'coffee_shop_count', 'rating_mean']]
            gm_df = gm_df.rename(columns={'coffee_shop_count': 'google_shop_count', 'rating_mean': 'google_rating'})
            
            fd_df = data['food_delivery_metrics_by_city'][['city', 'shop_count', 'rating_mean']]
            fd_df = fd_df.rename(columns={'shop_count': 'delivery_shop_count', 'rating_mean': 'delivery_rating'})
            
            tw_df = data['twitter_metrics_by_city'][['city', 'tweet_count', 'like_count_sum']]
            tw_df = tw_df.rename(columns={'tweet_count': 'twitter_mentions', 'like_count_sum': 'twitter_engagement'})
            
            # Merge the dataframes on city
            merged_df = pd.merge(gm_df, fd_df, on='city', how='outer')
            merged_df = pd.merge(merged_df, tw_df, on='city', how='outer')
            
            # Fill NA values
            merged_df = merged_df.fillna(0)
            
            # Compute correlations between sources
            correlation = merged_df.corr()
            
            city_results['cross_source'] = {
                'merged_data': merged_df.to_dict('records'),
                'correlation': correlation.to_dict()
            }
            
            # Regression analysis: Does social media activity predict coffee shop ratings?
            if all(col in merged_df.columns for col in ['twitter_mentions', 'google_rating']):
                X = merged_df['twitter_mentions'].values.reshape(-1, 1)
                y = merged_df['google_rating'].values
                
                if len(X) > 1 and len(y) > 1:  # Need at least 2 data points
                    try:
                        slope, intercept, r_value, p_value, std_err = stats.linregress(
                            merged_df['twitter_mentions'], merged_df['google_rating']
                        )
                        
                        city_results['cross_source']['regression'] = {
                            'slope': slope,
                            'intercept': intercept,
                            'r_squared': r_value**2,
                            'p_value': p_value,
                            'std_err': std_err
                        }
                    except Exception as e:
                        logger.error(f"Error performing regression analysis: {str(e)}")
        
        return city_results
    
    def analyze_pricing_data(self, data):
        """
        Analyze coffee pricing data.
        
        Args:
            data (dict): Dictionary of dataframes
            
        Returns:
            dict: Analysis results for pricing
        """
        logger.info("Analyzing coffee pricing data")
        
        price_results = {}
        
        # Analyze Coffee Prices from food delivery apps if available
        if 'food_delivery_coffee_prices' in data:
            df = data['food_delivery_coffee_prices']
            
            if not df.empty:
                # Summary statistics of prices
                price_stats = df.groupby('name')['price'].describe().reset_index()
                
                # Price comparison across cities
                city_comparison = df.pivot_table(
                    index='name', 
                    columns='city', 
                    values='price', 
                    aggfunc='mean'
                ).reset_index()
                
                price_results['coffee_menu_items'] = {
                    'summary_stats': price_stats.to_dict('records'),
                    'city_comparison': city_comparison.to_dict('records')
                }
                
                # Calculate price variability
                df['price_normalized'] = df.groupby('name')['price'].transform(
                    lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0
                )
                
                price_variability = df.groupby('city')['price_normalized'].agg(['mean', 'std']).reset_index()
                price_results['price_variability'] = price_variability.to_dict('records')
        
        # Analyze Price and Inflation comparison if available
        if 'price_inflation_comparison' in data:
            df = data['price_inflation_comparison']
            
            if not df.empty:
                # Correlation between coffee price, milk price, and inflation
                correlation = df[['coffee_index', 'milk_index', 'inflation_rate']].corr()
                
                # Monthly price change analysis
                monthly_changes = df[['month', 'coffee_index_change', 'milk_index_change', 'inflation_rate']].copy()
                
                # Calculate if price changes outpace inflation
                monthly_changes['coffee_vs_inflation'] = monthly_changes['coffee_index_change'] - monthly_changes['inflation_rate']
                monthly_changes['milk_vs_inflation'] = monthly_changes['milk_index_change'] - monthly_changes['inflation_rate']
                
                price_results['inflation_comparison'] = {
                    'correlation': correlation.to_dict(),
                    'monthly_changes': monthly_changes.to_dict('records'),
                    'avg_coffee_change': monthly_changes['coffee_index_change'].mean(),
                    'avg_milk_change': monthly_changes['milk_index_change'].mean(),
                    'avg_inflation': monthly_changes['inflation_rate'].mean(),
                    'months_coffee_above_inflation': (monthly_changes['coffee_vs_inflation'] > 0).sum(),
                    'months_milk_above_inflation': (monthly_changes['milk_vs_inflation'] > 0).sum(),
                    'total_months': len(monthly_changes)
                }
        
        # Price level distribution from Google Maps if available
        if 'google_maps_price_by_city' in data:
            df = data['google_maps_price_by_city']
            
            if not df.empty:
                # Count of shops by price level and city
                price_level_counts = df.pivot_table(
                    index='city', 
                    columns='price_level', 
                    values='count', 
                    aggfunc='sum'
                ).fillna(0).reset_index()
                
                # Calculate percentage of shops in each price level by city
                price_level_counts_pct = df.pivot_table(
                    index='city', 
                    columns='price_level', 
                    values='count', 
                    aggfunc='sum'
                ).fillna(0)
                
                price_level_counts_pct = price_level_counts_pct.div(price_level_counts_pct.sum(axis=1), axis=0) * 100
                price_level_counts_pct = price_level_counts_pct.reset_index()
                
                price_results['price_level_distribution'] = {
                    'counts': price_level_counts.to_dict('records'),
                    'percentage': price_level_counts_pct.to_dict('records')
                }
        
        return price_results
    
    def analyze_market_trends(self, data):
        """
        Analyze coffee market trend data.
        
        Args:
            data (dict): Dictionary of dataframes
            
        Returns:
            dict: Analysis results for market trends
        """
        logger.info("Analyzing coffee market trend data")
        
        trend_results = {}
        
        # Analyze consumption growth if available
        if 'consumption_growth' in data:
            df = data['consumption_growth']
            
            if not df.empty:
                # Calculate average annual growth rate
                avg_growth = df['yoy_growth'].mean()
                
                # Calculate compound annual growth rate (CAGR)
                years = df['year'].max() - df['year'].min()
                if years > 0:
                    start_consumption = df.loc[df['year'] == df['year'].min(), 'consumption_tons'].values[0]
                    end_consumption = df.loc[df['year'] == df['year'].max(), 'consumption_tons'].values[0]
                    cagr = (end_consumption / start_consumption) ** (1 / years) - 1
                    cagr *= 100  # Convert to percentage
                else:
                    cagr = None
                
                trend_results['consumption'] = {
                    'annual_growth': df[['year', 'consumption_tons', 'yoy_growth']].to_dict('records'),
                    'avg_annual_growth': avg_growth,
                    'cagr': cagr,
                    'latest_consumption': df.loc[df['year'] == df['year'].max(), 'consumption_tons'].values[0],
                    'latest_per_capita': df.loc[df['year'] == df['year'].max(), 'per_capita_kg'].values[0]
                }
        
        # Analyze competitor data if available
        if 'competitor_category_summary' in data:
            df = data['competitor_category_summary']
            
            if not df.empty:
                trend_results['competitors'] = {
                    'summary': df.to_dict('records')
                }
        
        # Analyze city presence if available
        if 'competitor_city_presence' in data:
            df = data['competitor_city_presence']
            
            if not df.empty:
                # Pivot table to get brand count by city and category
                city_pivot = df.pivot_table(
                    index='city', 
                    columns='category', 
                    values='brand_count', 
                    aggfunc='sum'
                ).fillna(0).reset_index()
                
                # Calculate market concentration by city
                df_concentration = df.copy()
                df_concentration['market_share'] = df_concentration.groupby('city')['brand_count'].transform(
                    lambda x: x / x.sum()
                )
                
                # Calculate Herfindahl-Hirschman Index (HHI) for market concentration
                hhi_by_city = df_concentration.groupby('city').apply(
                    lambda x: (x['market_share'] ** 2).sum() * 10000  # Scale to 0-10000
                ).reset_index()
                hhi_by_city.columns = ['city', 'hhi']
                
                # Categorize market concentration
                hhi_by_city['concentration'] = pd.cut(
                    hhi_by_city['hhi'],
                    bins=[0, 1500, 2500, 10000],
                    labels=['Low Concentration', 'Moderate Concentration', 'High Concentration']
                )
                
                trend_results['market_concentration'] = {
                    'city_category_counts': city_pivot.to_dict('records'),
                    'hhi_by_city': hhi_by_city.to_dict('records')
                }
        
        # Analyze social media trends if available
        if 'top_hashtags' in data and 'top_trends' in data:
            hashtags_df = data['top_hashtags']
            trends_df = data['top_trends']
            
            social_media_trends = {}
            
            if not hashtags_df.empty:
                social_media_trends['hashtags'] = hashtags_df.to_dict('records')
            
            if not trends_df.empty:
                social_media_trends['trends'] = trends_df.to_dict('records')
            
            if social_media_trends:
                trend_results['social_media'] = social_media_trends
                
                # If sentiment data is available
                if 'hashtag_sentiment' in data:
                    sentiment_df = data['hashtag_sentiment']
                    if not sentiment_df.empty:
                        trend_results['social_media']['sentiment'] = sentiment_df.to_dict('records')
        
        return trend_results
    
    def analyze_review_data(self, data):
        """
        Analyze coffee shop review data.
        
        Args:
            data (dict): Dictionary of dataframes
            
        Returns:
            dict: Analysis results for reviews
        """
        logger.info("Analyzing coffee shop review data")
        
        review_results = {}
        
        # Analyze Google Maps rating distribution if available
        if 'google_maps_rating_distribution' in data:
            df = data['google_maps_rating_distribution']
            
            if not df.empty:
                review_results['google_maps'] = {
                    'rating_distribution': df.to_dict('records'),
                    'total_ratings': df['count'].sum()
                }
        
        # Analyze food delivery review metrics if available
        if 'food_delivery_review_metrics' in data:
            df = data['food_delivery_review_metrics']
            
            if not df.empty:
                review_results['food_delivery'] = {
                    'metrics_by_city': df.to_dict('records'),
                    'overall_avg_rating': df['rating_mean'].mean(),
                    'total_reviews': df['rating_count'].sum()
                }
        
        # Compare ratings across platforms if both are available
        if 'google_maps' in review_results and 'food_delivery' in review_results:
            review_results['cross_platform'] = {
                'google_avg_rating': None,  # Would need to calculate from original data
                'delivery_avg_rating': review_results['food_delivery']['overall_avg_rating'],
                'rating_difference': None  # Would need both values
            }
        
        return review_results
    
    def perform_analysis(self):
        """
        Perform comprehensive statistical analysis on the data.
        
        Returns:
            dict: Analysis results
        """
        logger.info("Starting comprehensive statistical analysis")
        
        # Load the transformed data
        data = self.load_data()
        
        if not data:
            logger.warning("No data available for analysis")
            return {}
        
        # Perform various analyses
        results = {}
        
        # City-based analysis
        results['city_analysis'] = self.analyze_city_data(data)
        
        # Pricing analysis
        results['pricing_analysis'] = self.analyze_pricing_data(data)
        
        # Market trends analysis
        results['market_trends'] = self.analyze_market_trends(data)
        
        # Review analysis
        results['review_analysis'] = self.analyze_review_data(data)
        
        # Overall summary statistics
        results['summary'] = {
            'total_files_analyzed': len(data),
            'data_sources': list(data.keys()),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        self.analysis_results = results
        
        return results
    
    def save_results(self, output_dir, timestamp):
        """
        Save analysis results to JSON file.
        
        Args:
            output_dir (str): Directory to save results
            timestamp (str): Timestamp string for filename
        
        Returns:
            str: Path to saved results file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"statistical_analysis_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Analysis results saved to {output_file}")
        
        return output_file


def perform_statistical_analysis(processed_data, timestamp=None):
    """
    Perform statistical analysis on processed coffee shop data.
    
    Args:
        processed_data: Processed data (unused in this implementation as we load directly from files)
        timestamp (str, optional): Timestamp string. If None, current timestamp will be used.
    
    Returns:
        dict: Analysis results
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"Starting statistical analysis for timestamp {timestamp}")
    
    # Set paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    processed_dir = os.path.join(base_dir, PATHS['processed_data'])
    transformed_dir = os.path.join(processed_dir, f"transformed_{timestamp}")
    
    # Check if transformed directory exists, otherwise use latest
    if not os.path.exists(transformed_dir):
        logger.warning(f"Transformed data directory {transformed_dir} does not exist")
        transformed_dir = os.path.join(processed_dir, "transformed_latest")
        
        if not os.path.exists(transformed_dir):
            logger.error("No transformed data directory found")
            return {}
    
    # Initialize analyzer with transformed data directory
    analyzer = CoffeeShopAnalyzer(transformed_dir)
    
    # Perform analysis
    results = analyzer.perform_analysis()
    
    # Save results
    output_dir = os.path.join(base_dir, PATHS['processed_data'], f"analysis_{timestamp}")
    analyzer.save_results(output_dir, timestamp)
    
    return results


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run analysis with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    perform_statistical_analysis({}, timestamp)