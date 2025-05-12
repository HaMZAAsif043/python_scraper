"""
Module for collecting social media data related to coffee shops using free APIs and web scraping.
"""

import os
import json
import logging
import requests
import time
import random
from datetime import datetime, timedelta
import pandas as pd
import re
from bs4 import BeautifulSoup
from ..config import TARGET_LOCATIONS, PATHS

logger = logging.getLogger(__name__)

class TwitterDataCollector:
    """Class to handle collection of Twitter data using web scraping techniques."""
    
    def __init__(self):
        """Initialize the Twitter data collector."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_coffee_shop_tweets(self, query, location, max_tweets=100):
        """
        Search for tweets related to coffee shops in a given location.
        
        Args:
            query (str): Search query
            location (str): Location to search in
            max_tweets (int): Maximum number of tweets to collect
            
        Returns:
            list: List of tweets
        """
        # Note: Direct Twitter search scraping has become increasingly difficult
        # This is a simplified approach that would need frequent updates based on Twitter's changes
        # For a production system, you might want to consider a more robust solution
        
        logger.info(f"Searching for tweets with query: {query} in {location}")
        
        # Since direct Twitter scraping is complex, we'll use a simulated approach
        # In a real system, you might want to use third-party services, RSS feeds, or other public data sources
        
        # This is simulated data - in a real implementation we would scrape data from Twitter
        tweets = self._generate_simulated_tweets(query, location, max_tweets)
        
        logger.info(f"Retrieved {len(tweets)} tweets for query: {query} in {location}")
        return tweets
    
    def _generate_simulated_tweets(self, query, location, count):
        """
        Generate simulated tweets based on query parameters.
        This is a placeholder for actual Twitter data scraping, which requires more advanced techniques.
        
        Args:
            query (str): Search query
            location (str): Location
            count (int): Number of tweets to generate
            
        Returns:
            list: List of simulated tweets
        """
        tweets = []
        coffee_shop_names = [
            f"{location} Café", "Coffee Express", "Brew Haven", "Morning Cup", 
            "Espresso Lane", "Coffee Culture", "The Bean House", "Java Junction",
            "Coffee & Conversations", "The Roasted Bean", "Café Aroma"
        ]
        
        sentiments = ["Amazing coffee at", "Really loved the ambiance at", 
                     "Had a terrible experience at", "Just discovered", 
                     "Best latte I've had was at", "Overpriced coffee at",
                     "Great place to work from", "Friendly staff at", 
                     "The wifi is really good at", "Delicious pastries at"]
        
        hashtags = ["#coffee", "#coffeelover", "#café", "#coffeeaddict", 
                   "#morningcoffee", "#espresso", "#latte", "#cappuccino", 
                   "#coffeebreak", "#coffeeshop", "#specialtycoffee", 
                   "#latteart", "#barista", "#coffeeculture"]
        
        now = datetime.now()
        
        for i in range(min(count, 100)):  # Cap at 100 for simulated data
            shop = random.choice(coffee_shop_names)
            sentiment = random.choice(sentiments)
            selected_hashtags = random.sample(hashtags, random.randint(1, 3))
            hashtag_str = ' '.join(selected_hashtags)
            
            # Generate a time in the past 7 days
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            tweet_time = now - timedelta(days=days_ago, hours=hours_ago)
            
            # Generate random engagement metrics
            likes = random.randint(0, 50)
            retweets = random.randint(0, 10)
            comments = random.randint(0, 5)
            
            tweet = {
                'id': f"sim-{i}-{int(time.time())}",
                'text': f"{sentiment} {shop}! {hashtag_str}",
                'created_at': tweet_time.isoformat(),
                'user': {
                    'name': f"User{random.randint(1000, 9999)}",
                    'username': f"user_{random.randint(1000, 9999)}",
                    'followers_count': random.randint(50, 5000)
                },
                'metrics': {
                    'likes': likes,
                    'retweets': retweets,
                    'comments': comments
                },
                'location': location,
                'entities': {
                    'hashtags': [tag.replace('#', '') for tag in selected_hashtags]
                },
                'data_source': 'simulated_twitter_data'
            }
            tweets.append(tweet)
        
        return tweets
            

    def search_tweets(self, query, max_results=100, days_back=7):
        """
        Search for tweets related to coffee shops.
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of tweets to retrieve
            days_back (int): How many days back to search
            
        Returns:
            list: List of relevant tweets
        """
        if not self.bearer_token:
            logger.warning("Twitter bearer token not available, cannot search tweets")
            return []
            
        # Calculate start_time (7 days ago)
        start_time = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        endpoint = f"{self.base_url}/tweets/search/recent"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        params = {
            "query": query,
            "max_results": min(max_results, 100),  # API limit is 100 per request
            "start_time": start_time,
            "tweet.fields": "created_at,public_metrics,geo,lang",
            "user.fields": "name,username,location,verified,description,public_metrics",
            "expansions": "author_id,geo.place_id",
            "place.fields": "contained_within,country,country_code,full_name,geo,id,name,place_type"
        }
        
        try:
            logger.info(f"Searching tweets for query: {query}")
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            tweets = data.get('data', [])
            
            # Handle pagination if needed
            if len(tweets) < max_results and 'next_token' in data.get('meta', {}):
                remaining = max_results - len(tweets)
                next_token = data['meta']['next_token']
                
                while len(tweets) < max_results and next_token:
                    params['next_token'] = next_token
                    params['max_results'] = min(remaining, 100)
                    
                    response = requests.get(endpoint, headers=headers, params=params)
                    response.raise_for_status()
                    
                    more_data = response.json()
                    more_tweets = more_data.get('data', [])
                    tweets.extend(more_tweets)
                    
                    if 'next_token' in more_data.get('meta', {}):
                        next_token = more_data['meta']['next_token']
                        remaining = max_results - len(tweets)
                    else:
                        break
            
            logger.info(f"Retrieved {len(tweets)} tweets for query: {query}")
            return tweets
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching tweets: {str(e)}")
            return []
    
    def extract_hashtags(self, text):
        """Extract hashtags from text."""
        return re.findall(r'#(\w+)', text)
    
    def analyze_tweets(self, tweets):
        """
        Analyze tweets to extract relevant information.
        
        Args:
            tweets (list): List of tweet objects
            
        Returns:
            dict: Analysis results
        """
        if not tweets:
            return {}
            
        # Extract tweet metrics
        like_counts = [tweet.get('public_metrics', {}).get('like_count', 0) for tweet in tweets]
        retweet_counts = [tweet.get('public_metrics', {}).get('retweet_count', 0) for tweet in tweets]
        
        # Extract hashtags
        all_hashtags = []
        for tweet in tweets:
            text = tweet.get('text', '')
            hashtags = self.extract_hashtags(text)
            all_hashtags.extend(hashtags)
        
        # Count hashtag frequencies
        hashtag_counts = {}
        for tag in all_hashtags:
            tag = tag.lower()
            if tag in hashtag_counts:
                hashtag_counts[tag] += 1
            else:
                hashtag_counts[tag] = 1
        
        # Sort hashtags by frequency
        sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
        top_hashtags = sorted_hashtags[:20]  # Get top 20 hashtags
        
        return {
            'tweet_count': len(tweets),
            'avg_likes': sum(like_counts) / len(tweets) if tweets else 0,
            'avg_retweets': sum(retweet_counts) / len(tweets) if tweets else 0,
            'top_hashtags': top_hashtags
        }


class FacebookDataCollector:
    """Class to handle collection of coffee shop data from Facebook Graph API."""
    
    def __init__(self):
        """Initialize the collector with API key."""
        # Use environment variable if available, otherwise fallback to config
        self.api_key = None
    
    def search_coffee_shops(self, location, radius=5000):
        """
        Search for coffee shops on Facebook Pages.
        
        Args:
            location (str): Location string
            radius (int): Search radius in meters
            
        Returns:
            list: List of coffee shop pages
        """
        if not self.api_key:
            logger.warning("Facebook API key not provided, skipping Facebook search")
            return []
            
        # This is a simplified implementation for demonstration
        # In a real application, you would need to implement proper Facebook Graph API calls
        
        # Placeholder for demonstration
        logger.info(f"Searching Facebook Pages for coffee shops in {location}")
        logger.warning("Facebook Graph API implementation is a placeholder")
        
        # Return dummy data
        return [
            {
                "id": "123456789",
                "name": "Example Coffee Shop 1",
                "location": {"city": location.split(',')[0], "country": "Pakistan"},
                "rating": 4.5,
                "page_likes": 5000
            },
            {
                "id": "987654321",
                "name": "Example Coffee Shop 2",
                "location": {"city": location.split(',')[0], "country": "Pakistan"},
                "rating": 4.2,
                "page_likes": 3500
            }
        ]
    
    def get_page_details(self, page_id):
        """
        Get detailed information about a Facebook Page.
        
        Args:
            page_id (str): Facebook Page ID
            
        Returns:
            dict: Page details
        """
        if not self.api_key:
            return {}
            
        # Placeholder implementation
        logger.info(f"Getting Facebook Page details for {page_id}")
        
        # Return dummy data
        return {
            "id": page_id,
            "about": "A cozy coffee shop serving specialty coffee.",
            "website": "https://example.com",
            "phone": "+92 123 4567890",
            "hours": {
                "mon_1_open": "09:00",
                "mon_1_close": "22:00",
                # Other days would follow...
            },
            "price_range": "$$",
            "menu_url": "https://example.com/menu",
            "cover_photo": "https://example.com/cover.jpg",
            "profile_photo": "https://example.com/profile.jpg",
            "posts": [
                {"message": "Try our new seasonal blend!", "created_time": "2023-05-01T12:00:00Z", "likes": 45},
                {"message": "Holiday special menu available now!", "created_time": "2023-04-28T10:30:00Z", "likes": 32}
            ]
        }


def collect_social_media_data():
    """
    Collect coffee shop data from social media platforms.
    
    Returns:
        dict: Collected social media data
    """
    # Twitter data collection
    twitter_collector = TwitterDataCollector()
    twitter_data = {}
    
    search_queries = [
        "coffee shop Pakistan",
        "café Pakistan",
        "specialty coffee Pakistan",
        "best coffee Pakistan"
    ]
    
    for location in TARGET_LOCATIONS:
        city = location.split(',')[0]
        location_queries = [f"{q} {city}" for q in search_queries]
        
        location_tweets = []
        for query in location_queries:
            tweets = twitter_collector.search_tweets(query, max_results=100)
            location_tweets.extend(tweets)
        
        # Analyze tweets for this location
        twitter_data[city] = {
            'raw_tweets': location_tweets,
            'analysis': twitter_collector.analyze_tweets(location_tweets)
        }
    
    # Facebook data collection
    facebook_collector = FacebookDataCollector()
    facebook_data = {}
    
    for location in TARGET_LOCATIONS:
        city = location.split(',')[0]
        shops = facebook_collector.search_coffee_shops(location)
        
        # Get detailed information for each shop
        detailed_shops = []
        for shop in shops:
            page_id = shop.get('id')
            if page_id:
                details = facebook_collector.get_page_details(page_id)
                detailed_shops.append({**shop, **details})
        
        facebook_data[city] = detailed_shops
    
    # Combine all social media data
    social_media_data = {
        'twitter': twitter_data,
        'facebook': facebook_data
    }
    
    # Save raw data to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), PATHS['raw_data'])
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"social_media_{timestamp}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(social_media_data, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Saved social media data to {output_file}")
    
    return social_media_data


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Collect data
    collect_social_media_data()
