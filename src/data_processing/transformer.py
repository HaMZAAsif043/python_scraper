"""
Module for transforming cleaned data into analysis-ready formats.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from ..config import PATHS

logger = logging.getLogger(__name__)

def transform_google_maps_data(cleaned_dir, transformed_dir, timestamp):
    """
    Transform cleaned Google Maps data.
    
    Args:
        cleaned_dir (str): Directory with cleaned data
        transformed_dir (str): Directory for transformed data
        timestamp (str): Timestamp string
    
    Returns:
        dict: Dictionary with transformed DataFrames
    """
    logger.info("Transforming Google Maps data")
    
    # Look for cleaned Google Maps data
    google_files = [f for f in os.listdir(cleaned_dir) if f.startswith('google_maps_cleaned_') and f.endswith('.csv')]
    
    if not google_files:
        logger.warning("No cleaned Google Maps data found")
        return {}
    
    google_file = google_files[0]  # Take the first file if multiple exist
    google_df = pd.read_csv(os.path.join(cleaned_dir, google_file))
    
    if google_df.empty:
        logger.warning("Google Maps DataFrame is empty")
        return {}
    
    # Calculate average rating by city
    if all(col in google_df.columns for col in ['formatted_address', 'rating']):
        # Extract city from address (simple approach, adjust based on actual data format)
        google_df['city'] = google_df['formatted_address'].str.extract(r'([A-Za-z]+),\s*Pakistan')
        
        # Group by city and calculate metrics
        city_metrics = google_df.groupby('city').agg({
            'place_id': 'count',
            'rating': ['mean', 'median', 'std', 'min', 'max'],
            'user_ratings_total': 'sum'
        }).reset_index()
        
        # Flatten multi-level columns
        city_metrics.columns = ['_'.join(col).strip('_') for col in city_metrics.columns.values]
        city_metrics.rename(columns={'place_id_count': 'coffee_shop_count'}, inplace=True)
        
        # Save transformed data
        output_file = os.path.join(transformed_dir, f"google_maps_city_metrics_{timestamp}.csv")
        city_metrics.to_csv(output_file, index=False)
        logger.info(f"Saved transformed Google Maps city metrics to {output_file}")
    
    # Price level distribution
    if 'price_level' in google_df.columns:
        price_level_counts = google_df['price_level'].value_counts().reset_index()
        price_level_counts.columns = ['price_level', 'count']
        
        if 'city' in google_df.columns:
            price_by_city = google_df.groupby(['city', 'price_level']).size().reset_index(name='count')
            
            output_file = os.path.join(transformed_dir, f"google_maps_price_by_city_{timestamp}.csv")
            price_by_city.to_csv(output_file, index=False)
            logger.info(f"Saved transformed Google Maps price level by city to {output_file}")
    
    # Rating distribution
    if 'rating' in google_df.columns:
        # Create rating bins
        google_df['rating_bin'] = pd.cut(
            google_df['rating'],
            bins=[0, 1, 2, 3, 4, 5],
            labels=['0-1', '1-2', '2-3', '3-4', '4-5'],
            right=True
        )
        
        rating_dist = google_df['rating_bin'].value_counts().reset_index()
        rating_dist.columns = ['rating_range', 'count']
        rating_dist = rating_dist.sort_values('rating_range')
        
        output_file = os.path.join(transformed_dir, f"google_maps_rating_distribution_{timestamp}.csv")
        rating_dist.to_csv(output_file, index=False)
        logger.info(f"Saved transformed Google Maps rating distribution to {output_file}")
    
    # Return a dictionary with transformed DataFrames
    return {
        'city_metrics': city_metrics if 'city_metrics' in locals() else None,
        'price_by_city': price_by_city if 'price_by_city' in locals() else None,
        'rating_distribution': rating_dist if 'rating_dist' in locals() else None
    }


def transform_social_media_data(cleaned_dir, transformed_dir, timestamp):
    """
    Transform cleaned social media data.
    
    Args:
        cleaned_dir (str): Directory with cleaned data
        transformed_dir (str): Directory for transformed data
        timestamp (str): Timestamp string
    
    Returns:
        dict: Dictionary with transformed DataFrames
    """
    logger.info("Transforming social media data")
    
    transformed_data = {}
    
    # Look for cleaned Twitter data
    twitter_files = [f for f in os.listdir(cleaned_dir) if f.startswith('twitter_') and f.endswith('.csv')]
    
    if twitter_files:
        # Aggregate data across cities
        all_twitter_dfs = []
        
        for twitter_file in twitter_files:
            twitter_df = pd.read_csv(os.path.join(cleaned_dir, twitter_file))
            
            # Extract city from filename
            city_match = twitter_file.split('_')[1]
            twitter_df['city'] = city_match
            
            all_twitter_dfs.append(twitter_df)
        
        if all_twitter_dfs:
            # Combine all city data
            combined_twitter = pd.concat(all_twitter_dfs, ignore_index=True)
            
            # Calculate metrics for each city
            if 'like_count' in combined_twitter.columns and 'retweet_count' in combined_twitter.columns:
                twitter_metrics_by_city = combined_twitter.groupby('city').agg({
                    'text': 'count',
                    'like_count': ['mean', 'sum'],
                    'retweet_count': ['mean', 'sum']
                }).reset_index()
                
                # Flatten multi-level columns
                twitter_metrics_by_city.columns = ['_'.join(col).strip('_') for col in twitter_metrics_by_city.columns.values]
                twitter_metrics_by_city.rename(columns={'text_count': 'tweet_count'}, inplace=True)
                
                output_file = os.path.join(transformed_dir, f"twitter_metrics_by_city_{timestamp}.csv")
                twitter_metrics_by_city.to_csv(output_file, index=False)
                logger.info(f"Saved transformed Twitter metrics by city to {output_file}")
                
                transformed_data['twitter_metrics_by_city'] = twitter_metrics_by_city
            
            # Perform text analysis to extract coffee-related keywords
            if 'text' in combined_twitter.columns:
                # Simple keyword counting (in a real implementation, you would use more sophisticated NLP)
                keywords = ['coffee', 'café', 'espresso', 'latte', 'cappuccino', 'brew']
                
                for keyword in keywords:
                    combined_twitter[f'has_{keyword}'] = combined_twitter['text'].str.contains(
                        keyword, case=False, na=False
                    ).astype(int)
                
                # Count keywords by city
                keyword_cols = [f'has_{keyword}' for keyword in keywords]
                keyword_counts = combined_twitter.groupby('city')[keyword_cols].sum().reset_index()
                
                # Reshape to long format for easier plotting
                keyword_counts_long = pd.melt(
                    keyword_counts,
                    id_vars=['city'],
                    value_vars=keyword_cols,
                    var_name='keyword',
                    value_name='count'
                )
                
                # Clean up keyword names
                keyword_counts_long['keyword'] = keyword_counts_long['keyword'].str.replace('has_', '')
                
                output_file = os.path.join(transformed_dir, f"twitter_keywords_by_city_{timestamp}.csv")
                keyword_counts_long.to_csv(output_file, index=False)
                logger.info(f"Saved transformed Twitter keyword counts to {output_file}")
                
                transformed_data['twitter_keywords'] = keyword_counts_long
    
    # Look for cleaned Facebook data
    facebook_files = [f for f in os.listdir(cleaned_dir) if f.startswith('facebook_') and f.endswith('.csv')]
    
    if facebook_files:
        # Similar process as Twitter data
        all_facebook_dfs = []
        
        for facebook_file in facebook_files:
            facebook_df = pd.read_csv(os.path.join(cleaned_dir, facebook_file))
            
            # Extract city from filename
            city_match = facebook_file.split('_')[1]
            facebook_df['city'] = city_match
            
            all_facebook_dfs.append(facebook_df)
        
        if all_facebook_dfs:
            # Combine all city data
            combined_facebook = pd.concat(all_facebook_dfs, ignore_index=True)
            
            # Calculate metrics by city
            if 'page_likes' in combined_facebook.columns and 'rating' in combined_facebook.columns:
                facebook_metrics_by_city = combined_facebook.groupby('city').agg({
                    'name': 'count',
                    'page_likes': ['mean', 'sum', 'median'],
                    'rating': ['mean', 'min', 'max']
                }).reset_index()
                
                # Flatten multi-level columns
                facebook_metrics_by_city.columns = ['_'.join(col).strip('_') for col in facebook_metrics_by_city.columns.values]
                facebook_metrics_by_city.rename(columns={'name_count': 'page_count'}, inplace=True)
                
                output_file = os.path.join(transformed_dir, f"facebook_metrics_by_city_{timestamp}.csv")
                facebook_metrics_by_city.to_csv(output_file, index=False)
                logger.info(f"Saved transformed Facebook metrics by city to {output_file}")
                
                transformed_data['facebook_metrics_by_city'] = facebook_metrics_by_city
    
    return transformed_data


def transform_food_delivery_data(cleaned_dir, transformed_dir, timestamp):
    """
    Transform cleaned food delivery data.
    
    Args:
        cleaned_dir (str): Directory with cleaned data
        transformed_dir (str): Directory for transformed data
        timestamp (str): Timestamp string
    
    Returns:
        dict: Dictionary with transformed DataFrames
    """
    logger.info("Transforming food delivery data")
    
    transformed_data = {}
    
    # Look for cleaned food delivery shops data
    shop_files = [f for f in os.listdir(cleaned_dir) if f.startswith('food_delivery_') and f.endswith('_shops_cleaned_' + timestamp + '.csv')]
    
    # Combine shops data from all cities
    if shop_files:
        all_shops_dfs = []
        
        for shop_file in shop_files:
            shop_df = pd.read_csv(os.path.join(cleaned_dir, shop_file))
            
            # Extract city from filename
            city_match = shop_file.split('_')[2]
            if 'city' not in shop_df.columns:
                shop_df['city'] = city_match
            
            all_shops_dfs.append(shop_df)
        
        if all_shops_dfs:
            # Combine all city data
            combined_shops = pd.concat(all_shops_dfs, ignore_index=True)
            
            # Calculate metrics by city
            if 'rating' in combined_shops.columns:
                delivery_metrics_by_city = combined_shops.groupby('city').agg({
                    'id': 'count',
                    'rating': ['mean', 'median', 'min', 'max']
                }).reset_index()
                
                # Flatten multi-level columns
                delivery_metrics_by_city.columns = ['_'.join(col).strip('_') for col in delivery_metrics_by_city.columns.values]
                delivery_metrics_by_city.rename(columns={'id_count': 'shop_count'}, inplace=True)
                
                output_file = os.path.join(transformed_dir, f"food_delivery_metrics_by_city_{timestamp}.csv")
                delivery_metrics_by_city.to_csv(output_file, index=False)
                logger.info(f"Saved transformed food delivery metrics by city to {output_file}")
                
                transformed_data['delivery_metrics_by_city'] = delivery_metrics_by_city
    
    # Look for cleaned menu items data
    menu_files = [f for f in os.listdir(cleaned_dir) if f.startswith('food_delivery_') and f.endswith('_menu_cleaned_' + timestamp + '.csv')]
    
    # Analyze menu items and prices
    if menu_files:
        all_menu_dfs = []
        
        for menu_file in menu_files:
            menu_df = pd.read_csv(os.path.join(cleaned_dir, menu_file))
            all_menu_dfs.append(menu_df)
        
        if all_menu_dfs:
            # Combine all menu data
            combined_menu = pd.concat(all_menu_dfs, ignore_index=True)
            
            # Calculate average prices by city and item
            if 'price' in combined_menu.columns and 'name' in combined_menu.columns:
                # Top menu items
                top_items = combined_menu['name'].value_counts().reset_index()
                top_items.columns = ['item_name', 'count']
                top_items = top_items.head(20)  # Top 20 items
                
                output_file = os.path.join(transformed_dir, f"food_delivery_top_items_{timestamp}.csv")
                top_items.to_csv(output_file, index=False)
                logger.info(f"Saved transformed food delivery top items to {output_file}")
                
                transformed_data['top_menu_items'] = top_items
                
                # Average prices by city
                price_by_city = combined_menu.groupby('city')['price'].agg(['mean', 'median', 'min', 'max']).reset_index()
                
                output_file = os.path.join(transformed_dir, f"food_delivery_price_by_city_{timestamp}.csv")
                price_by_city.to_csv(output_file, index=False)
                logger.info(f"Saved transformed food delivery price by city to {output_file}")
                
                transformed_data['price_by_city'] = price_by_city
                
                # Common coffee items prices
                coffee_items = combined_menu[combined_menu['name'].str.contains('|'.join(['Espresso', 'Latte', 'Cappuccino', 'Americano', 'Mocha']), case=False, na=False)]
                
                if not coffee_items.empty:
                    coffee_prices = coffee_items.groupby(['city', 'name'])['price'].mean().reset_index()
                    
                    output_file = os.path.join(transformed_dir, f"food_delivery_coffee_prices_{timestamp}.csv")
                    coffee_prices.to_csv(output_file, index=False)
                    logger.info(f"Saved transformed coffee prices to {output_file}")
                    
                    transformed_data['coffee_prices'] = coffee_prices
    
    # Look for cleaned reviews data
    review_files = [f for f in os.listdir(cleaned_dir) if f.startswith('food_delivery_') and f.endswith('_reviews_cleaned_' + timestamp + '.csv')]
    
    # Analyze reviews
    if review_files:
        all_review_dfs = []
        
        for review_file in review_files:
            review_df = pd.read_csv(os.path.join(cleaned_dir, review_file))
            all_review_dfs.append(review_df)
        
        if all_review_dfs:
            # Combine all review data
            combined_reviews = pd.concat(all_review_dfs, ignore_index=True)
            
            # Calculate average review metrics by city
            if 'rating' in combined_reviews.columns:
                review_metrics_by_city = combined_reviews.groupby('city').agg({
                    'rating': ['mean', 'count', 'median', 'std']
                }).reset_index()
                
                # Flatten multi-level columns
                review_metrics_by_city.columns = ['_'.join(col).strip('_') for col in review_metrics_by_city.columns.values]
                
                output_file = os.path.join(transformed_dir, f"food_delivery_review_metrics_{timestamp}.csv")
                review_metrics_by_city.to_csv(output_file, index=False)
                logger.info(f"Saved transformed review metrics to {output_file}")
                
                transformed_data['review_metrics'] = review_metrics_by_city
    
    return transformed_data


def transform_market_trends_data(cleaned_dir, transformed_dir, timestamp):
    """
    Transform cleaned market trends data.
    
    Args:
        cleaned_dir (str): Directory with cleaned data
        transformed_dir (str): Directory for transformed data
        timestamp (str): Timestamp string
    
    Returns:
        dict: Dictionary with transformed DataFrames
    """
    logger.info("Transforming market trends data")
    
    transformed_data = {}
    
    # Load consumption stats
    consumption_files = [f for f in os.listdir(cleaned_dir) if f.startswith('consumption_stats_cleaned_') and f.endswith('.csv')]
    
    if consumption_files:
        consumption_df = pd.read_csv(os.path.join(cleaned_dir, consumption_files[0]))
        
        if not consumption_df.empty:
            # Year-over-year growth rates
            if 'consumption_tons' in consumption_df.columns and 'year' in consumption_df.columns:
                consumption_df = consumption_df.sort_values('year')
                consumption_df['prev_year_consumption'] = consumption_df['consumption_tons'].shift(1)
                consumption_df['yoy_growth'] = (consumption_df['consumption_tons'] - consumption_df['prev_year_consumption']) / consumption_df['prev_year_consumption'] * 100
                
                # Remove first row which has no growth calculation
                consumption_growth = consumption_df.dropna(subset=['yoy_growth'])
                
                output_file = os.path.join(transformed_dir, f"consumption_growth_{timestamp}.csv")
                consumption_growth.to_csv(output_file, index=False)
                logger.info(f"Saved transformed consumption growth data to {output_file}")
                
                transformed_data['consumption_growth'] = consumption_growth
    
    # Load price index data
    price_files = [f for f in os.listdir(cleaned_dir) if f.startswith('coffee_price_index_cleaned_') and f.endswith('.csv')]
    milk_files = [f for f in os.listdir(cleaned_dir) if f.startswith('milk_price_index_cleaned_') and f.endswith('.csv')]
    inflation_files = [f for f in os.listdir(cleaned_dir) if f.startswith('general_inflation_cleaned_') and f.endswith('.csv')]
    
    if price_files and milk_files and inflation_files:
        coffee_price_df = pd.read_csv(os.path.join(cleaned_dir, price_files[0]))
        milk_price_df = pd.read_csv(os.path.join(cleaned_dir, milk_files[0]))
        inflation_df = pd.read_csv(os.path.join(cleaned_dir, inflation_files[0]))
        
        # Combine the three datasets into one for comparison
        if not coffee_price_df.empty and not milk_price_df.empty and not inflation_df.empty:
            coffee_price_df = coffee_price_df.rename(columns={'index': 'coffee_index'})
            milk_price_df = milk_price_df.rename(columns={'index': 'milk_index'})
            inflation_df = inflation_df.rename(columns={'rate': 'inflation_rate'})
            
            # Merge all three datasets
            price_comparison = pd.merge(coffee_price_df, milk_price_df, on='month', how='outer')
            price_comparison = pd.merge(price_comparison, inflation_df, on='month', how='outer')
            
            # Calculate monthly price changes
            for col in ['coffee_index', 'milk_index']:
                price_comparison[f'{col}_prev'] = price_comparison[col].shift(1)
                price_comparison[f'{col}_change'] = (price_comparison[col] - price_comparison[f'{col}_prev']) / price_comparison[f'{col}_prev'] * 100
            
            price_comparison = price_comparison.drop(['coffee_index_prev', 'milk_index_prev'], axis=1)
            price_comparison = price_comparison.dropna()
            
            output_file = os.path.join(transformed_dir, f"price_inflation_comparison_{timestamp}.csv")
            price_comparison.to_csv(output_file, index=False)
            logger.info(f"Saved transformed price and inflation comparison to {output_file}")
            
            transformed_data['price_inflation_comparison'] = price_comparison
    
    # Load competitors data
    competitor_files = [f for f in os.listdir(cleaned_dir) if f.startswith('competitors_cleaned_') and f.endswith('.csv')]
    
    if competitor_files:
        competitors_df = pd.read_csv(os.path.join(cleaned_dir, competitor_files[0]))
        
        if not competitors_df.empty:
            # Analyze competitor distribution by category
            if 'category' in competitors_df.columns and 'stores_count' in competitors_df.columns:
                category_summary = competitors_df.groupby('category').agg({
                    'name': 'count',
                    'stores_count': ['sum', 'mean']
                }).reset_index()
                
                # Flatten multi-level columns
                category_summary.columns = ['_'.join(col).strip('_') for col in category_summary.columns.values]
                category_summary.rename(columns={
                    'name_count': 'brand_count',
                    'stores_count_sum': 'total_stores',
                    'stores_count_mean': 'avg_stores_per_brand'
                }, inplace=True)
                
                output_file = os.path.join(transformed_dir, f"competitor_category_summary_{timestamp}.csv")
                category_summary.to_csv(output_file, index=False)
                logger.info(f"Saved transformed competitor category summary to {output_file}")
                
                transformed_data['competitor_category_summary'] = category_summary
            
            # Create a city distribution dataset
            if 'cities' in competitors_df.columns:
                # This assumes 'cities' is a string representation of a list
                city_data = []
                
                for _, row in competitors_df.iterrows():
                    brand = row['name']
                    category = row['category']
                    stores = row['stores_count']
                    
                    # Safely evaluate string list (in a real implementation, the data structure would be better defined)
                    try:
                        # Remove brackets, quotes, and split by commas
                        cities_str = row['cities'].strip("[]'\"").replace("'", "").replace('"', '')
                        cities = [city.strip() for city in cities_str.split(',')]
                        
                        for city in cities:
                            city_data.append({
                                'brand': brand,
                                'category': category,
                                'city': city,
                                'presence': 1
                            })
                    except:
                        logger.warning(f"Could not parse cities for brand {brand}")
                
                if city_data:
                    city_presence_df = pd.DataFrame(city_data)
                    city_brand_counts = city_presence_df.groupby(['city', 'category']).size().reset_index(name='brand_count')
                    
                    output_file = os.path.join(transformed_dir, f"competitor_city_presence_{timestamp}.csv")
                    city_brand_counts.to_csv(output_file, index=False)
                    logger.info(f"Saved transformed competitor city presence to {output_file}")
                    
                    transformed_data['competitor_city_presence'] = city_brand_counts
    
    # Load social trends data
    hashtag_files = [f for f in os.listdir(cleaned_dir) if f.startswith('trending_hashtags_cleaned_') and f.endswith('.csv')]
    trends_files = [f for f in os.listdir(cleaned_dir) if f.startswith('popular_trends_cleaned_') and f.endswith('.csv')]
    
    if hashtag_files:
        hashtags_df = pd.read_csv(os.path.join(cleaned_dir, hashtag_files[0]))
        
        if not hashtags_df.empty:
            # Top hashtags
            top_hashtags = hashtags_df.sort_values('mentions', ascending=False).head(10)
            
            output_file = os.path.join(transformed_dir, f"top_hashtags_{timestamp}.csv")
            top_hashtags.to_csv(output_file, index=False)
            logger.info(f"Saved transformed top hashtags to {output_file}")
            
            transformed_data['top_hashtags'] = top_hashtags
            
            # Sentiment distribution
            if 'sentiment' in hashtags_df.columns:
                sentiment_counts = hashtags_df.groupby('sentiment').agg({
                    'tag': 'count',
                    'mentions': 'sum'
                }).reset_index()
                
                output_file = os.path.join(transformed_dir, f"hashtag_sentiment_{timestamp}.csv")
                sentiment_counts.to_csv(output_file, index=False)
                logger.info(f"Saved transformed hashtag sentiment to {output_file}")
                
                transformed_data['hashtag_sentiment'] = sentiment_counts
    
    if trends_files:
        trends_df = pd.read_csv(os.path.join(cleaned_dir, trends_files[0]))
        
        if not trends_df.empty:
            # Sort trends by growth percentage
            top_trends = trends_df.sort_values('growth_percentage', ascending=False)
            
            output_file = os.path.join(transformed_dir, f"top_trends_{timestamp}.csv")
            top_trends.to_csv(output_file, index=False)
            logger.info(f"Saved transformed top trends to {output_file}")
            
            transformed_data['top_trends'] = top_trends
    
    return transformed_data


def transform_data(timestamp):
    """
    Transform cleaned data into analysis-ready formats.
    
    Args:
        timestamp (str): Timestamp string
    
    Returns:
        dict: Dictionary containing paths to transformed data files
    """
    logger.info(f"Starting data transformation process for timestamp {timestamp}")
    
    # Create output directory for transformed data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    processed_dir = os.path.join(base_dir, PATHS['processed_data'])
    cleaned_dir = os.path.join(processed_dir, f"cleaned_{timestamp}")
    transformed_dir = os.path.join(processed_dir, f"transformed_{timestamp}")
    
    # Check if cleaned data directory exists
    if not os.path.exists(cleaned_dir):
        logger.warning(f"Cleaned data directory {cleaned_dir} does not exist")
        cleaned_dir = os.path.join(processed_dir, "cleaned_latest")
        
        if not os.path.exists(cleaned_dir):
            logger.error("No cleaned data directory found")
            return {}
    
    # Create transformed data directory
    os.makedirs(transformed_dir, exist_ok=True)
    
    # Transform each type of data
    transformed_data = {}
    
    # Google Maps data
    google_transformed = transform_google_maps_data(cleaned_dir, transformed_dir, timestamp)
    if google_transformed:
        transformed_data['google_maps'] = google_transformed
    
    # Social media data
    social_transformed = transform_social_media_data(cleaned_dir, transformed_dir, timestamp)
    if social_transformed:
        transformed_data['social_media'] = social_transformed
    
    # Food delivery data
    delivery_transformed = transform_food_delivery_data(cleaned_dir, transformed_dir, timestamp)
    if delivery_transformed:
        transformed_data['food_delivery'] = delivery_transformed
    
    # Market trends data
    market_transformed = transform_market_trends_data(cleaned_dir, transformed_dir, timestamp)
    if market_transformed:
        transformed_data['market_trends'] = market_transformed
    
    # Save a manifest of the transformed data
    manifest = {
        'timestamp': timestamp,
        'transformed_data_sources': list(transformed_data.keys()),
        'files_generated': [f for f in os.listdir(transformed_dir) if os.path.isfile(os.path.join(transformed_dir, f))]
    }
    
    manifest_file = os.path.join(transformed_dir, 'manifest.json')
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Data transformation completed. Manifest saved to {manifest_file}")
    
    # Create a symlink or copy to "latest" for convenience
    latest_dir = os.path.join(processed_dir, "transformed_latest")
    if os.path.exists(latest_dir) and os.path.isdir(latest_dir):
        import shutil
        shutil.rmtree(latest_dir)
    
    try:
        # Symlink on Unix-like systems
        os.symlink(transformed_dir, latest_dir)
    except:
        # On Windows, just copy the directory
        import shutil
        shutil.copytree(transformed_dir, latest_dir)
    
    logger.info(f"Created link/copy to 'transformed_latest' for convenient access")
    
    return manifest


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Transform data with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transform_data(timestamp)
