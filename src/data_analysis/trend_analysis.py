"""
Module for trend analysis of coffee shop data.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from ..config import PATHS

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Class to handle trend analysis of coffee shop data."""
    
    def __init__(self, data_dir):
        """
        Initialize the analyzer with the directory containing transformed data.
        
        Args:
            data_dir (str): Path to the directory containing transformed data
        """
        self.data_dir = data_dir
        self.results = {}
    
    def load_time_series_data(self):
        """
        Load time series data for trend analysis.
        
        Returns:
            dict: Dictionary of time series dataframes
        """
        logger.info(f"Loading time series data from {self.data_dir}")
        
        time_series_data = {}
        
        # Look for time series data files
        for file in os.listdir(self.data_dir):
            if any(pattern in file for pattern in ['price_index', 'inflation', 'consumption']):
                file_path = os.path.join(self.data_dir, file)
                try:
                    # Use the filename without extension as the key
                    key = file.rsplit('.', 1)[0]
                    df = pd.read_csv(file_path)
                    
                    # Check if it has time-related columns
                    if any(col in df.columns for col in ['month', 'year', 'date']):
                        time_series_data[key] = df
                        logger.info(f"Loaded time series data {key} with shape {df.shape}")
                except Exception as e:
                    logger.error(f"Error loading {file}: {str(e)}")
        
        return time_series_data
    
    def prepare_time_series(self, df, date_column, value_column):
        """
        Prepare a dataframe for time series analysis.
        
        Args:
            df (pd.DataFrame): Input dataframe
            date_column (str): Column containing date information
            value_column (str): Column containing values to analyze
            
        Returns:
            pd.Series: Prepared time series
        """
        # Convert to datetime if not already
        if df[date_column].dtype != 'datetime64[ns]':
            try:
                # Handle different date formats
                if 'month' in date_column:
                    df['date'] = pd.to_datetime(df[date_column], format='%Y-%m')
                else:
                    df['date'] = pd.to_datetime(df[date_column])
            except Exception:
                logger.error(f"Could not convert {date_column} to datetime")
                return None
        
        # Sort by date
        df = df.sort_values('date')
        
        # Set date as index and select value column
        ts = df.set_index('date')[value_column]
        
        return ts
    
    def analyze_price_trends(self, data):
        """
        Analyze price trends over time.
        
        Args:
            data (dict): Dictionary of time series dataframes
            
        Returns:
            dict: Price trend analysis results
        """
        logger.info("Analyzing price trends")
        
        price_results = {}
        
        # Analyze coffee price index if available
        coffee_price_files = [key for key in data.keys() if 'coffee_price_index' in key]
        
        if coffee_price_files:
            df = data[coffee_price_files[0]]
            
            if not df.empty and 'month' in df.columns and 'coffee_index' in df.columns:
                # Prepare time series
                coffee_ts = self.prepare_time_series(df, 'month', 'coffee_index')
                
                if coffee_ts is not None:
                    # Calculate growth rate
                    coffee_ts = coffee_ts.astype(float)
                    coffee_growth = coffee_ts.pct_change() * 100
                    
                    # Calculate statistical properties
                    avg_monthly_growth = coffee_growth.mean()
                    volatility = coffee_growth.std()
                    
                    # Check for stationarity using ADF test
                    try:
                        adf_result = adfuller(coffee_ts.dropna())
                        is_stationary = adf_result[1] < 0.05  # p-value < 0.05 means stationary
                    except Exception:
                        is_stationary = None
                    
                    # Decompose series into trend, seasonal, and residual components
                    try:
                        # Need enough periods for decomposition (at least 2 complete cycles)
                        if len(coffee_ts) >= 24:  # Assuming monthly data
                            decomposition = seasonal_decompose(coffee_ts, model='additive', period=12)
                            
                            trend = decomposition.trend.dropna()
                            seasonal = decomposition.seasonal.dropna()
                            residual = decomposition.resid.dropna()
                            
                            # Convert to lists for JSON serialization
                            trend_data = [{'date': date.strftime('%Y-%m'), 'value': value} 
                                         for date, value in zip(trend.index, trend.values)]
                            seasonal_data = [{'date': date.strftime('%Y-%m'), 'value': value} 
                                           for date, value in zip(seasonal.index, seasonal.values)]
                            
                            decomposition_results = {
                                'trend': trend_data[:12],  # Limit to first year for brevity
                                'seasonal_pattern': seasonal_data[:12],
                                'trend_direction': 'increasing' if trend.iloc[-1] > trend.iloc[0] else 'decreasing',
                                'seasonality_strength': seasonal.std() / residual.std() if residual.std() > 0 else 0
                            }
                        else:
                            decomposition_results = {'error': 'Not enough data for decomposition'}
                    except Exception as e:
                        logger.error(f"Error in time series decomposition: {str(e)}")
                        decomposition_results = {'error': str(e)}
                    
                    # Future forecasting using ARIMA
                    try:
                        # Simple ARIMA model (p,d,q) = (1,1,1)
                        if len(coffee_ts) >= 12:  # Need at least a year of data
                            model = ARIMA(coffee_ts, order=(1,1,1))
                            model_fit = model.fit()
                            
                            # Forecast next 6 months
                            forecast = model_fit.forecast(steps=6)
                            
                            forecast_data = [{'date': date.strftime('%Y-%m'), 'value': value} 
                                           for date, value in zip(forecast.index, forecast.values)]
                            
                            forecast_results = {
                                'forecast': forecast_data,
                                'forecast_direction': 'increasing' if forecast[-1] > coffee_ts.iloc[-1] else 'decreasing'
                            }
                        else:
                            forecast_results = {'error': 'Not enough data for forecasting'}
                    except Exception as e:
                        logger.error(f"Error in ARIMA forecasting: {str(e)}")
                        forecast_results = {'error': str(e)}
                    
                    price_results['coffee_price'] = {
                        'avg_monthly_growth': avg_monthly_growth,
                        'volatility': volatility,
                        'is_stationary': is_stationary,
                        'decomposition': decomposition_results,
                        'forecast': forecast_results
                    }
        
        # Analyze milk price index if available (similar approach)
        milk_price_files = [key for key in data.keys() if 'milk_price_index' in key]
        
        if milk_price_files:
            df = data[milk_price_files[0]]
            
            if not df.empty and 'month' in df.columns and 'milk_index' in df.columns:
                # Similar analysis as coffee price, but simplified here
                milk_ts = self.prepare_time_series(df, 'month', 'milk_index')
                
                if milk_ts is not None:
                    milk_ts = milk_ts.astype(float)
                    milk_growth = milk_ts.pct_change() * 100
                    
                    price_results['milk_price'] = {
                        'avg_monthly_growth': milk_growth.mean(),
                        'volatility': milk_growth.std(),
                        'latest_value': milk_ts.iloc[-1],
                        'first_value': milk_ts.iloc[0],
                        'overall_growth': ((milk_ts.iloc[-1] / milk_ts.iloc[0]) - 1) * 100 if milk_ts.iloc[0] > 0 else None
                    }
        
        # Compare prices with inflation if available
        inflation_files = [key for key in data.keys() if 'inflation' in key]
        price_inflation_files = [key for key in data.keys() if 'price_inflation_comparison' in key]
        
        if price_inflation_files:
            df = data[price_inflation_files[0]]
            
            if not df.empty:
                # Calculate correlation between prices and inflation
                if all(col in df.columns for col in ['coffee_index', 'milk_index', 'inflation_rate']):
                    correlation = df[['coffee_index', 'milk_index', 'inflation_rate']].corr()
                    
                    price_results['inflation_comparison'] = {
                        'correlation': correlation.to_dict(),
                        'interpretation': {
                            'coffee_inflation_corr': 'strong' if abs(correlation.loc['coffee_index', 'inflation_rate']) > 0.7 
                                                else 'moderate' if abs(correlation.loc['coffee_index', 'inflation_rate']) > 0.3 
                                                else 'weak',
                            'milk_inflation_corr': 'strong' if abs(correlation.loc['milk_index', 'inflation_rate']) > 0.7 
                                               else 'moderate' if abs(correlation.loc['milk_index', 'inflation_rate']) > 0.3 
                                               else 'weak'
                        }
                    }
        
        return price_results
    
    def analyze_consumption_trends(self, data):
        """
        Analyze coffee consumption trends.
        
        Args:
            data (dict): Dictionary of time series dataframes
            
        Returns:
            dict: Consumption trend analysis results
        """
        logger.info("Analyzing consumption trends")
        
        consumption_results = {}
        
        # Analyze consumption data if available
        consumption_files = [key for key in data.keys() if 'consumption' in key]
        
        if consumption_files:
            df = data[consumption_files[0]]
            
            if not df.empty and 'year' in df.columns and 'consumption_tons' in df.columns:
                # Prepare time series
                cons_ts = self.prepare_time_series(df, 'year', 'consumption_tons')
                
                if cons_ts is not None:
                    # Calculate year-over-year growth
                    yoy_growth = cons_ts.pct_change() * 100
                    
                    # Calculate compound annual growth rate (CAGR)
                    years = (cons_ts.index[-1] - cons_ts.index[0]).days / 365
                    if years > 0:
                        cagr = (cons_ts.iloc[-1] / cons_ts.iloc[0]) ** (1 / years) - 1
                        cagr *= 100  # Convert to percentage
                    else:
                        cagr = None
                    
                    # Linear regression to find trend
                    x = np.arange(len(cons_ts)).reshape(-1, 1)
                    y = cons_ts.values
                    
                    from sklearn.linear_model import LinearRegression
                    model = LinearRegression()
                    model.fit(x, y)
                    
                    trend = model.predict(x)
                    slope = model.coef_[0]
                    
                    consumption_results['overall'] = {
                        'cagr': cagr,
                        'avg_yoy_growth': yoy_growth.mean(),
                        'trend_slope': slope,
                        'trend_direction': 'increasing' if slope > 0 else 'decreasing',
                        'latest_value': cons_ts.iloc[-1],
                        'first_value': cons_ts.iloc[0],
                        'total_growth': ((cons_ts.iloc[-1] / cons_ts.iloc[0]) - 1) * 100
                    }
                    
                    # ARIMA forecasting
                    try:
                        if len(cons_ts) >= 5:  # Need at least 5 years of data
                            model = ARIMA(cons_ts, order=(1,1,0))
                            model_fit = model.fit()
                            
                            # Forecast next 3 years
                            forecast = model_fit.forecast(steps=3)
                            
                            forecast_data = [{'year': date.year, 'value': value} 
                                          for date, value in zip(forecast.index, forecast.values)]
                            
                            consumption_results['forecast'] = {
                                'next_3_years': forecast_data,
                                'forecast_direction': 'increasing' if forecast[-1] > cons_ts.iloc[-1] else 'decreasing'
                            }
                    except Exception as e:
                        logger.error(f"Error in consumption forecasting: {str(e)}")
                        consumption_results['forecast'] = {'error': str(e)}
                
                # Per capita analysis if available
                if 'per_capita_kg' in df.columns:
                    per_capita_ts = self.prepare_time_series(df, 'year', 'per_capita_kg')
                    
                    if per_capita_ts is not None:
                        per_capita_growth = per_capita_ts.pct_change() * 100
                        
                        consumption_results['per_capita'] = {
                            'avg_growth': per_capita_growth.mean(),
                            'latest_value': per_capita_ts.iloc[-1],
                            'first_value': per_capita_ts.iloc[0],
                            'total_growth': ((per_capita_ts.iloc[-1] / per_capita_ts.iloc[0]) - 1) * 100
                        }
                        
                        # Compare with global averages (dummy data, would need actual comparison in real implementation)
                        consumption_results['global_comparison'] = {
                            'global_avg_per_capita': 1.2,  # Dummy value
                            'comparison': 'below' if per_capita_ts.iloc[-1] < 1.2 else 'above',
                            'difference_percentage': ((per_capita_ts.iloc[-1] / 1.2) - 1) * 100
                        }
        
        return consumption_results
    
    def analyze_social_media_trends(self, data):
        """
        Analyze social media trends related to coffee shops.
        
        Args:
            data (dict): Dictionary of dataframes
            
        Returns:
            dict: Social media trend analysis results
        """
        logger.info("Analyzing social media trends")
        
        social_results = {}
        
        # Look for hashtag data
        hashtag_files = [key for key in data.keys() if 'hashtag' in key or 'trend' in key]
        
        if hashtag_files:
            # Analyze top hashtags if available
            top_hashtags = None
            sentiment = None
            
            for file_key in hashtag_files:
                df = data[file_key]
                
                if 'hashtag' in file_key and 'tag' in df.columns and 'mentions' in df.columns:
                    top_hashtags = df.sort_values('mentions', ascending=False).head(10)
                
                if 'sentiment' in file_key and 'sentiment' in df.columns:
                    sentiment = df
            
            if top_hashtags is not None:
                # Analyze hashtag distribution
                total_mentions = top_hashtags['mentions'].sum()
                top_hashtags['percentage'] = top_hashtags['mentions'] / total_mentions * 100
                
                social_results['hashtags'] = {
                    'top_10': top_hashtags[['tag', 'mentions', 'percentage']].to_dict('records'),
                    'total_mentions': total_mentions
                }
                
                # Categorize hashtags
                categories = {
                    'experience': ['coffee', 'coffeetime', 'coffeelover', 'café', 'cafe', 'specialtycoffee'],
                    'location': ['coffeeshop', 'pakistan', 'karachi', 'lahore', 'islamabad'],
                    'product': ['espresso', 'latte', 'cappuccino', 'coldbrew', 'mocha', 'brew', 'beans'],
                    'lifestyle': ['morning', 'work', 'study', 'book', 'friends', 'weekend']
                }
                
                # Count hashtags in each category
                category_counts = {category: 0 for category in categories}
                
                for _, row in top_hashtags.iterrows():
                    tag = row['tag'].lower().replace('#', '')
                    for category, keywords in categories.items():
                        if any(keyword in tag for keyword in keywords):
                            category_counts[category] += row['mentions']
                            break
                
                social_results['hashtag_categories'] = [
                    {'category': category, 'count': count} for category, count in category_counts.items()
                ]
            
            # Analyze sentiment if available
            if sentiment is not None and 'sentiment' in sentiment.columns:
                sentiment_counts = sentiment.groupby('sentiment').agg({
                    'tag': 'count',
                    'mentions': 'sum'
                }).reset_index()
                
                total = sentiment_counts['mentions'].sum()
                sentiment_counts['percentage'] = sentiment_counts['mentions'] / total * 100
                
                social_results['sentiment'] = {
                    'distribution': sentiment_counts.to_dict('records'),
                    'overall_sentiment': 'positive' if sentiment_counts.loc[sentiment_counts['sentiment'] == 'positive', 'percentage'].values[0] > 50 else 'negative'
                }
        
        return social_results
    
    def analyze_competitor_trends(self, data):
        """
        Analyze competitor trends in the coffee shop market.
        
        Args:
            data (dict): Dictionary of dataframes
            
        Returns:
            dict: Competitor trend analysis results
        """
        logger.info("Analyzing competitor trends")
        
        competitor_results = {}
        
        # Look for competitor data
        competitor_files = [key for key in data.keys() if 'competitor' in key]
        
        if competitor_files:
            # Analyze competitor summary if available
            summary_file = next((key for key in competitor_files if 'summary' in key), None)
            presence_file = next((key for key in competitor_files if 'presence' in key), None)
            
            if summary_file:
                df = data[summary_file]
                
                if not df.empty and 'category' in df.columns:
                    # Compare major chains vs local brands
                    if all(col in df.columns for col in ['category', 'brand_count', 'total_stores']):
                        comparison = df.pivot_table(
                            index='category',
                            values=['brand_count', 'total_stores', 'avg_stores_per_brand'],
                            aggfunc='sum'
                        ).reset_index()
                        
                        competitor_results['chain_vs_local'] = comparison.to_dict('records')
                        
                        # Calculate market share percentages
                        total_stores = comparison['total_stores'].sum()
                        comparison['market_share'] = comparison['total_stores'] / total_stores * 100
                        
                        competitor_results['market_share'] = comparison[['category', 'market_share']].to_dict('records')
            
            if presence_file:
                df = data[presence_file]
                
                if not df.empty and all(col in df.columns for col in ['city', 'category', 'brand_count']):
                    # Analyze geographical distribution of competitors
                    geo_distribution = df.pivot_table(
                        index='city',
                        columns='category',
                        values='brand_count',
                        aggfunc='sum'
                    ).fillna(0).reset_index()
                    
                    # Calculate market concentration
                    hhi_by_city = df.groupby('city').apply(
                        lambda group: (group['brand_count'] ** 2).sum() / (group['brand_count'].sum() ** 2) * 10000
                    ).reset_index()
                    hhi_by_city.columns = ['city', 'hhi']
                    
                    # Categorize market concentration
                    hhi_by_city['concentration'] = pd.cut(
                        hhi_by_city['hhi'],
                        bins=[0, 1500, 2500, 10000],
                        labels=['Low Concentration', 'Moderate Concentration', 'High Concentration']
                    )
                    
                    competitor_results['geographical'] = {
                        'distribution': geo_distribution.to_dict('records'),
                        'concentration': hhi_by_city.to_dict('records')
                    }
                    
                    # Identify expansion opportunities based on low competition areas
                    low_competition = hhi_by_city.sort_values('hhi', ascending=True).head(3)
                    
                    competitor_results['opportunities'] = {
                        'low_competition_cities': low_competition[['city', 'hhi', 'concentration']].to_dict('records')
                    }
        
        return competitor_results
    
    def analyze_trends(self):
        """
        Perform comprehensive trend analysis.
        
        Returns:
            dict: Comprehensive trend analysis results
        """
        logger.info("Starting comprehensive trend analysis")
        
        # Load time series data
        time_series_data = self.load_time_series_data()
        
        # Load all transformed data files
        all_data = {}
        
        for file in os.listdir(self.data_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(self.data_dir, file)
                try:
                    key = file.rsplit('.', 1)[0]
                    df = pd.read_csv(file_path)
                    all_data[key] = df
                except Exception as e:
                    logger.error(f"Error loading {file}: {str(e)}")
        
        # Perform various trend analyses
        results = {}
        
        # Price trends
        results['price_trends'] = self.analyze_price_trends(time_series_data)
        
        # Consumption trends
        results['consumption_trends'] = self.analyze_consumption_trends(time_series_data)
        
        # Social media trends
        results['social_media_trends'] = self.analyze_social_media_trends(all_data)
        
        # Competitor trends
        results['competitor_trends'] = self.analyze_competitor_trends(all_data)
        
        # Overall trend summary
        results['summary'] = {
            'timestamp': datetime.now().isoformat(),
            'key_insights': []
        }
        
        # Add key insights based on the analyses
        if results['price_trends'] and 'coffee_price' in results['price_trends']:
            if results['price_trends']['coffee_price'].get('forecast', {}).get('forecast_direction') == 'increasing':
                results['summary']['key_insights'].append("Coffee prices are projected to rise in the coming months.")
        
        if results['consumption_trends'] and 'forecast' in results['consumption_trends']:
            direction = results['consumption_trends']['forecast'].get('forecast_direction')
            if direction:
                insight = f"Coffee consumption in Pakistan is forecasted to {direction} in the next 3 years."
                results['summary']['key_insights'].append(insight)
        
        if results['competitor_trends'] and 'opportunities' in results['competitor_trends']:
            cities = [city['city'] for city in results['competitor_trends']['opportunities'].get('low_competition_cities', [])]
            if cities:
                insight = f"Market expansion opportunities identified in cities with low competition: {', '.join(cities)}."
                results['summary']['key_insights'].append(insight)
        
        if results['social_media_trends'] and 'sentiment' in results['social_media_trends']:
            sentiment = results['social_media_trends']['sentiment'].get('overall_sentiment')
            if sentiment:
                insight = f"Overall social media sentiment about coffee shops in Pakistan is {sentiment}."
                results['summary']['key_insights'].append(insight)
        
        self.results = results
        
        return results
    
    def save_results(self, output_dir, timestamp):
        """
        Save trend analysis results to a JSON file.
        
        Args:
            output_dir (str): Directory to save results
            timestamp (str): Timestamp string for filename
            
        Returns:
            str: Path to saved results file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"trend_analysis_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Trend analysis results saved to {output_file}")
        
        return output_file


def analyze_trends(processed_data, timestamp=None):
    """
    Perform trend analysis on processed coffee shop data.
    
    Args:
        processed_data: Processed data (unused in this implementation as we load directly from files)
        timestamp (str, optional): Timestamp string. If None, current timestamp will be used.
    
    Returns:
        dict: Trend analysis results
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"Starting trend analysis for timestamp {timestamp}")
    
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
    analyzer = TrendAnalyzer(transformed_dir)
    
    # Perform trend analysis
    results = analyzer.analyze_trends()
    
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
    analyze_trends({}, timestamp)
