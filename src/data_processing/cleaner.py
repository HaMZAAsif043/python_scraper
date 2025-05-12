"""
Module for cleaning raw data collected from various sources.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from ..config import PATHS

logger = logging.getLogger(__name__)

def clean_google_maps_data(data, output_dir, timestamp):
    """
    Clean and normalize Google Maps data.
    
    Args:
        data (list): Raw Google Maps data
        output_dir (str): Output directory
        timestamp (str): Timestamp string
    
    Returns:
        pd.DataFrame: Cleaned Google Maps data
    """
    logger.info("Cleaning Google Maps data")
    
    if not data:
        logger.warning("No Google Maps data to clean")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Handle missing values
    if 'rating' in df.columns:
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df['rating'].fillna(0, inplace=True)
    
    if 'user_ratings_total' in df.columns:
        df['user_ratings_total'] = pd.to_numeric(df['user_ratings_total'], errors='coerce')
        df['user_ratings_total'].fillna(0, inplace=True)
    
    if 'price_level' in df.columns:
        df['price_level'] = pd.to_numeric(df['price_level'], errors='coerce')
        df['price_level'].fillna(0, inplace=True)
    
    # Extract latitude and longitude if nested
    if 'location' in df.columns and df['location'].apply(lambda x: isinstance(x, dict)).any():
        df['latitude'] = df['location'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
        df['longitude'] = df['location'].apply(lambda x: x.get('lng') if isinstance(x, dict) else None)
    
    # Flatten nested data structures (simple approach)
    # In a real implementation, you might want a more sophisticated approach for nested data
    if 'reviews' in df.columns:
        df['reviews_count'] = df['reviews'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        df['avg_review_rating'] = df['reviews'].apply(
            lambda x: sum(r.get('rating', 0) for r in x) / len(x) if isinstance(x, list) and len(x) > 0 else 0
        )
    
    # Save cleaned data
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"google_maps_cleaned_{timestamp}.csv")
    
    # Select columns to save (excluding complex nested structures)
    columns_to_save = [col for col in df.columns if col not in ['reviews', 'photos', 'popular_times']]
    df[columns_to_save].to_csv(output_file, index=False)
    
    logger.info(f"Saved cleaned Google Maps data to {output_file}")
    
    return df


def clean_social_media_data(data, output_dir, timestamp):
    """
    Clean and normalize social media data.
    
    Args:
        data (dict): Raw social media data
        output_dir (str): Output directory
        timestamp (str): Timestamp string
    
    Returns:
        dict: Cleaned social media data with DataFrames
    """
    logger.info("Cleaning social media data")
    
    if not data:
        logger.warning("No social media data to clean")
        return {}
    
    cleaned_data = {}
    
    # Clean Twitter data
    if 'twitter' in data:
        twitter_data = data['twitter']
        twitter_dfs = {}
        
        for city, city_data in twitter_data.items():
            if 'raw_tweets' in city_data and city_data['raw_tweets']:
                # Convert tweets to DataFrame
                tweets_df = pd.DataFrame(city_data['raw_tweets'])
                
                # Basic cleaning
                if 'text' in tweets_df.columns:
                    # Remove newlines and extra spaces
                    tweets_df['text'] = tweets_df['text'].str.replace('\n', ' ').str.replace('\r', ' ')
                    tweets_df['text'] = tweets_df['text'].str.strip()
                
                # Extract metrics if nested
                if 'public_metrics' in tweets_df.columns and tweets_df['public_metrics'].apply(lambda x: isinstance(x, dict)).any():
                    for metric in ['retweet_count', 'reply_count', 'like_count', 'quote_count']:
                        tweets_df[metric] = tweets_df['public_metrics'].apply(
                            lambda x: x.get(metric, 0) if isinstance(x, dict) else 0
                        )
                
                # Save cleaned tweets
                twitter_dfs[city] = tweets_df
                output_file = os.path.join(output_dir, f"twitter_{city}_cleaned_{timestamp}.csv")
                tweets_df.to_csv(output_file, index=False)
                logger.info(f"Saved cleaned Twitter data for {city} to {output_file}")
        
        cleaned_data['twitter'] = twitter_dfs
    
    # Clean Facebook data
    if 'facebook' in data:
        facebook_data = data['facebook']
        facebook_dfs = {}
        
        for city, shops in facebook_data.items():
            if shops:
                # Convert to DataFrame
                shops_df = pd.DataFrame(shops)
                
                # Basic cleaning
                if 'rating' in shops_df.columns:
                    shops_df['rating'] = pd.to_numeric(shops_df['rating'], errors='coerce')
                    shops_df['rating'].fillna(0, inplace=True)
                
                if 'page_likes' in shops_df.columns:
                    shops_df['page_likes'] = pd.to_numeric(shops_df['page_likes'], errors='coerce')
                    shops_df['page_likes'].fillna(0, inplace=True)
                
                # Save cleaned data
                facebook_dfs[city] = shops_df
                output_file = os.path.join(output_dir, f"facebook_{city}_cleaned_{timestamp}.csv")
                shops_df.to_csv(output_file, index=False)
                logger.info(f"Saved cleaned Facebook data for {city} to {output_file}")
        
        cleaned_data['facebook'] = facebook_dfs
    
    return cleaned_data


def clean_food_delivery_data(data, output_dir, timestamp):
    """
    Clean and normalize food delivery data.
    
    Args:
        data (dict): Raw food delivery data
        output_dir (str): Output directory
        timestamp (str): Timestamp string
    
    Returns:
        dict: Cleaned food delivery data with DataFrames
    """
    logger.info("Cleaning food delivery data")
    
    if not data:
        logger.warning("No food delivery data to clean")
        return {}
    
    cleaned_data = {}
    
    for city, shops in data.items():
        if not shops:
            continue
        
        # Convert shops to DataFrame
        shops_df = pd.DataFrame(shops)
        
        # Basic cleaning
        if 'rating' in shops_df.columns:
            shops_df['rating'] = pd.to_numeric(shops_df['rating'], errors='coerce')
            shops_df['rating'].fillna(0, inplace=True)
        
        # Create a DataFrame for menu items (flattening nested data)
        menu_items = []
        for i, shop in enumerate(shops):
            if 'menu_items' in shop and isinstance(shop['menu_items'], list):
                for item in shop['menu_items']:
                    menu_item = {
                        'shop_id': shop.get('id', f"shop_{i}"),
                        'shop_name': shop.get('name', ''),
                        'city': city
                    }
                    menu_item.update(item)
                    menu_items.append(menu_item)
        
        menu_df = pd.DataFrame(menu_items) if menu_items else pd.DataFrame()
        
        # Create a DataFrame for reviews (flattening nested data)
        reviews = []
        for i, shop in enumerate(shops):
            if 'reviews' in shop and isinstance(shop['reviews'], list):
                for review in shop['reviews']:
                    review_item = {
                        'shop_id': shop.get('id', f"shop_{i}"),
                        'shop_name': shop.get('name', ''),
                        'city': city
                    }
                    review_item.update(review)
                    reviews.append(review_item)
        
        reviews_df = pd.DataFrame(reviews) if reviews else pd.DataFrame()
        
        # Save cleaned data
        cleaned_data[city] = {
            'shops': shops_df,
            'menu_items': menu_df,
            'reviews': reviews_df
        }
        
        # Save to CSV
        if not shops_df.empty:
            output_file = os.path.join(output_dir, f"food_delivery_{city}_shops_cleaned_{timestamp}.csv")
            shops_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned food delivery shops data for {city} to {output_file}")
        
        if not menu_df.empty:
            output_file = os.path.join(output_dir, f"food_delivery_{city}_menu_cleaned_{timestamp}.csv")
            menu_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned food delivery menu data for {city} to {output_file}")
        
        if not reviews_df.empty:
            output_file = os.path.join(output_dir, f"food_delivery_{city}_reviews_cleaned_{timestamp}.csv")
            reviews_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned food delivery reviews data for {city} to {output_file}")
    
    return cleaned_data


def clean_market_trends_data(data, output_dir, timestamp):
    """
    Clean and normalize market trends data.
    
    Args:
        data (dict): Raw market trends data
        output_dir (str): Output directory
        timestamp (str): Timestamp string
    
    Returns:
        dict: Cleaned market trends data with DataFrames
    """
    logger.info("Cleaning market trends data")
    
    if not data:
        logger.warning("No market trends data to clean")
        return {}
    
    cleaned_data = {}
    
    # Clean consumption stats
    if 'consumption_stats' in data and 'yearly_consumption' in data['consumption_stats']:
        consumption_df = pd.DataFrame(data['consumption_stats']['yearly_consumption'])
        consumption_df['year'] = pd.to_numeric(consumption_df['year'], errors='coerce')
        consumption_df['consumption_tons'] = pd.to_numeric(consumption_df['consumption_tons'], errors='coerce')
        consumption_df['per_capita_kg'] = pd.to_numeric(consumption_df['per_capita_kg'], errors='coerce')
        
        cleaned_data['consumption'] = consumption_df
        
        output_file = os.path.join(output_dir, f"consumption_stats_cleaned_{timestamp}.csv")
        consumption_df.to_csv(output_file, index=False)
        logger.info(f"Saved cleaned consumption stats data to {output_file}")
    
    # Clean inflation and price trends
    if 'inflation_price_trends' in data:
        inflation_data = data['inflation_price_trends']
        
        if 'coffee_beans_price_index' in inflation_data:
            coffee_price_df = pd.DataFrame(inflation_data['coffee_beans_price_index'])
            coffee_price_df['index'] = pd.to_numeric(coffee_price_df['index'], errors='coerce')
            
            cleaned_data['coffee_price'] = coffee_price_df
            
            output_file = os.path.join(output_dir, f"coffee_price_index_cleaned_{timestamp}.csv")
            coffee_price_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned coffee price index data to {output_file}")
        
        if 'milk_price_index' in inflation_data:
            milk_price_df = pd.DataFrame(inflation_data['milk_price_index'])
            milk_price_df['index'] = pd.to_numeric(milk_price_df['index'], errors='coerce')
            
            cleaned_data['milk_price'] = milk_price_df
            
            output_file = os.path.join(output_dir, f"milk_price_index_cleaned_{timestamp}.csv")
            milk_price_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned milk price index data to {output_file}")
        
        if 'general_inflation' in inflation_data:
            inflation_df = pd.DataFrame(inflation_data['general_inflation'])
            inflation_df['rate'] = pd.to_numeric(inflation_df['rate'], errors='coerce')
            
            cleaned_data['inflation'] = inflation_df
            
            output_file = os.path.join(output_dir, f"general_inflation_cleaned_{timestamp}.csv")
            inflation_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned general inflation data to {output_file}")
    
    # Clean competitor intelligence
    if 'competitor_intelligence' in data:
        competitor_data = data['competitor_intelligence']
        
        if 'major_chains' in competitor_data:
            chains_df = pd.DataFrame(competitor_data['major_chains'])
            chains_df['category'] = 'major_chain'
            
            if 'local_brands' in competitor_data:
                local_df = pd.DataFrame(competitor_data['local_brands'])
                local_df['category'] = 'local_brand'
                chains_df = pd.concat([chains_df, local_df], ignore_index=True)
            
            cleaned_data['competitors'] = chains_df
            
            output_file = os.path.join(output_dir, f"competitors_cleaned_{timestamp}.csv")
            chains_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned competitors data to {output_file}")
        
        if 'new_openings' in competitor_data:
            openings_df = pd.DataFrame(competitor_data['new_openings'])
            
            cleaned_data['new_openings'] = openings_df
            
            output_file = os.path.join(output_dir, f"new_openings_cleaned_{timestamp}.csv")
            openings_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned new openings data to {output_file}")
    
    # Clean social trends
    if 'social_trends' in data:
        social_data = data['social_trends']
        
        if 'trending_hashtags' in social_data:
            hashtags_df = pd.DataFrame(social_data['trending_hashtags'])
            hashtags_df['mentions'] = pd.to_numeric(hashtags_df['mentions'], errors='coerce')
            
            cleaned_data['hashtags'] = hashtags_df
            
            output_file = os.path.join(output_dir, f"trending_hashtags_cleaned_{timestamp}.csv")
            hashtags_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned hashtags data to {output_file}")
        
        if 'popular_trends' in social_data:
            trends_df = pd.DataFrame(social_data['popular_trends'])
            trends_df['growth_percentage'] = pd.to_numeric(trends_df['growth_percentage'], errors='coerce')
            
            cleaned_data['trends'] = trends_df
            
            output_file = os.path.join(output_dir, f"popular_trends_cleaned_{timestamp}.csv")
            trends_df.to_csv(output_file, index=False)
            logger.info(f"Saved cleaned trends data to {output_file}")
    
    return cleaned_data


def clean_data(raw_data, timestamp):
    """
    Clean and normalize data from all sources.
    
    Args:
        raw_data (dict): Dictionary containing raw data from different sources
        timestamp (str): Timestamp string
    
    Returns:
        dict: Dictionary containing cleaned data
    """
    logger.info(f"Starting data cleaning process for timestamp {timestamp}")
    
    # Create output directory for cleaned data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    processed_dir = os.path.join(base_dir, PATHS['processed_data'])
    cleaned_dir = os.path.join(processed_dir, f"cleaned_{timestamp}")
    os.makedirs(cleaned_dir, exist_ok=True)
    
    cleaned_data = {}
    
    # If raw_data is provided, use it directly
    if raw_data:
        if 'google' in raw_data and raw_data['google']:
            cleaned_data['google_maps'] = clean_google_maps_data(raw_data['google'], cleaned_dir, timestamp)
        
        if 'social' in raw_data and raw_data['social']:
            cleaned_data['social_media'] = clean_social_media_data(raw_data['social'], cleaned_dir, timestamp)
        
        if 'delivery' in raw_data and raw_data['delivery']:
            cleaned_data['food_delivery'] = clean_food_delivery_data(raw_data['delivery'], cleaned_dir, timestamp)
        
        if 'market' in raw_data and raw_data['market']:
            cleaned_data['market_trends'] = clean_market_trends_data(raw_data['market'], cleaned_dir, timestamp)
    
    # Otherwise, try to load the latest raw data files
    else:
        raw_dir = os.path.join(base_dir, PATHS['raw_data'])
        if not os.path.exists(raw_dir):
            logger.warning(f"Raw data directory {raw_dir} does not exist")
            return cleaned_data
        
        # Load Google Maps data
        google_files = [f for f in os.listdir(raw_dir) if f.startswith('google_maps_') and f.endswith('.json')]
        if google_files:
            latest_google_file = sorted(google_files, reverse=True)[0]
            try:
                with open(os.path.join(raw_dir, latest_google_file), 'r', encoding='utf-8') as f:
                    google_data = json.load(f)
                cleaned_data['google_maps'] = clean_google_maps_data(google_data, cleaned_dir, timestamp)
            except Exception as e:
                logger.error(f"Error cleaning Google Maps data: {str(e)}")
        
        # Load social media data
        social_files = [f for f in os.listdir(raw_dir) if f.startswith('social_media_') and f.endswith('.json')]
        if social_files:
            latest_social_file = sorted(social_files, reverse=True)[0]
            try:
                with open(os.path.join(raw_dir, latest_social_file), 'r', encoding='utf-8') as f:
                    social_data = json.load(f)
                cleaned_data['social_media'] = clean_social_media_data(social_data, cleaned_dir, timestamp)
            except Exception as e:
                logger.error(f"Error cleaning social media data: {str(e)}")
        
        # Load food delivery data
        delivery_files = [f for f in os.listdir(raw_dir) if f.startswith('food_delivery_') and f.endswith('.json')]
        if delivery_files:
            latest_delivery_file = sorted(delivery_files, reverse=True)[0]
            try:
                with open(os.path.join(raw_dir, latest_delivery_file), 'r', encoding='utf-8') as f:
                    delivery_data = json.load(f)
                cleaned_data['food_delivery'] = clean_food_delivery_data(delivery_data, cleaned_dir, timestamp)
            except Exception as e:
                logger.error(f"Error cleaning food delivery data: {str(e)}")
        
        # Load market trends data
        market_files = [f for f in os.listdir(raw_dir) if f.startswith('market_trends_') and f.endswith('.json')]
        if market_files:
            latest_market_file = sorted(market_files, reverse=True)[0]
            try:
                with open(os.path.join(raw_dir, latest_market_file), 'r', encoding='utf-8') as f:
                    market_data = json.load(f)
                cleaned_data['market_trends'] = clean_market_trends_data(market_data, cleaned_dir, timestamp)
            except Exception as e:
                logger.error(f"Error cleaning market trends data: {str(e)}")
    
    # Save a manifest of the cleaned data
    manifest = {
        'timestamp': timestamp,
        'cleaned_data_sources': list(cleaned_data.keys()),
        'files_generated': [f for f in os.listdir(cleaned_dir) if os.path.isfile(os.path.join(cleaned_dir, f))]
    }
    
    manifest_file = os.path.join(cleaned_dir, 'manifest.json')
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Data cleaning completed. Manifest saved to {manifest_file}")
    
    return cleaned_data


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Clean data with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_data({}, timestamp)
