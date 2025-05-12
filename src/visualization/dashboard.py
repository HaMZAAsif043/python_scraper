"""
Module for visualizing coffee shop data analysis results.
"""

import os
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..config import PATHS

# Set up matplotlib styling
plt.style.use('ggplot')
sns.set_style('whitegrid')
sns.set_palette('bright')

logger = logging.getLogger(__name__)

class CoffeeShopVisualizer:
    """Class to handle visualization of coffee shop data."""
    
    def __init__(self, analysis_dir):
        """
        Initialize the visualizer with the directory containing analysis results.
        
        Args:
            analysis_dir (str): Path to the directory containing analysis results
        """
        self.analysis_dir = analysis_dir
        self.statistical_results = None
        self.trend_results = None
        self.figures = {}
    
    def load_analysis_results(self):
        """
        Load analysis results from JSON files.
        
        Returns:
            bool: True if loading was successful, False otherwise
        """
        logger.info(f"Loading analysis results from {self.analysis_dir}")
        
        try:
            # Look for statistical analysis results
            for file in os.listdir(self.analysis_dir):
                if 'statistical_analysis' in file and file.endswith('.json'):
                    with open(os.path.join(self.analysis_dir, file), 'r', encoding='utf-8') as f:
                        self.statistical_results = json.load(f)
                    logger.info(f"Loaded statistical analysis results from {file}")
                    break
            
            # Look for trend analysis results
            for file in os.listdir(self.analysis_dir):
                if 'trend_analysis' in file and file.endswith('.json'):
                    with open(os.path.join(self.analysis_dir, file), 'r', encoding='utf-8') as f:
                        self.trend_results = json.load(f)
                    logger.info(f"Loaded trend analysis results from {file}")
                    break
            
            return True if self.statistical_results or self.trend_results else False
            
        except Exception as e:
            logger.error(f"Error loading analysis results: {str(e)}")
            return False
    
    def create_city_comparison_chart(self, output_file=None):
        """
        Create a chart comparing coffee shop metrics across cities.
        
        Args:
            output_file (str, optional): Output file path for the chart
            
        Returns:
            str: Path to the saved chart or None if failed
        """
        if not self.statistical_results or 'city_analysis' not in self.statistical_results:
            logger.warning("No city analysis data available for visualization")
            return None
        
        try:
            city_data = self.statistical_results['city_analysis']
            
            if 'google_maps' in city_data and 'shop_count_by_city' in city_data['google_maps']:
                shop_counts = pd.DataFrame(city_data['google_maps']['shop_count_by_city'])
                
                if not shop_counts.empty:
                    plt.figure(figsize=(12, 6))
                    ax = sns.barplot(data=shop_counts, x='city', y='coffee_shop_count')
                    
                    # Add value labels on top of bars
                    for i, v in enumerate(shop_counts['coffee_shop_count']):
                        ax.text(i, v + 0.1, str(v), ha='center')
                    
                    plt.title('Coffee Shop Count by City', fontsize=16)
                    plt.xlabel('City', fontsize=12)
                    plt.ylabel('Number of Coffee Shops', fontsize=12)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    # Save the figure if output file is provided
                    if output_file:
                        plt.savefig(output_file, dpi=300, bbox_inches='tight')
                        logger.info(f"Saved city comparison chart to {output_file}")
                        self.figures['city_comparison'] = output_file
                    
                    return output_file
                    
        except Exception as e:
            logger.error(f"Error creating city comparison chart: {str(e)}")
            return None
    
    def create_rating_distribution_chart(self, output_file=None):
        """
        Create a chart showing rating distribution of coffee shops.
        
        Args:
            output_file (str, optional): Output file path for the chart
            
        Returns:
            str: Path to the saved chart or None if failed
        """
        if not self.statistical_results or 'review_analysis' not in self.statistical_results:
            logger.warning("No review analysis data available for visualization")
            return None
        
        try:
            review_data = self.statistical_results['review_analysis']
            
            if 'google_maps' in review_data and 'rating_distribution' in review_data['google_maps']:
                ratings = pd.DataFrame(review_data['google_maps']['rating_distribution'])
                
                if not ratings.empty and 'rating' in ratings.columns and 'count' in ratings.columns:
                    plt.figure(figsize=(10, 6))
                    ax = sns.barplot(data=ratings, x='rating', y='count', color='skyblue')
                    
                    # Add value labels on top of bars
                    for i, v in enumerate(ratings['count']):
                        ax.text(i, v + 0.1, str(v), ha='center')
                    
                    plt.title('Rating Distribution of Coffee Shops', fontsize=16)
                    plt.xlabel('Rating', fontsize=12)
                    plt.ylabel('Count', fontsize=12)
                    plt.tight_layout()
                    
                    # Save the figure if output file is provided
                    if output_file:
                        plt.savefig(output_file, dpi=300, bbox_inches='tight')
                        logger.info(f"Saved rating distribution chart to {output_file}")
                        self.figures['rating_distribution'] = output_file
                    
                    return output_file
                    
        except Exception as e:
            logger.error(f"Error creating rating distribution chart: {str(e)}")
            return None
    
    def create_price_trend_chart(self, output_file=None):
        """
        Create a chart showing coffee price trends over time.
        
        Args:
            output_file (str, optional): Output file path for the chart
            
        Returns:
            str: Path to the saved chart or None if failed
        """
        if not self.trend_results or 'price_trends' not in self.trend_results:
            logger.warning("No price trend data available for visualization")
            return None
        
        try:
            price_data = self.trend_results['price_trends']
            
            if 'coffee_price' in price_data and 'forecast' in price_data['coffee_price']:
                forecast = price_data['coffee_price']['forecast']
                
                if isinstance(forecast, dict) and 'forecast' in forecast:
                    # Convert to DataFrame
                    forecast_df = pd.DataFrame(forecast['forecast'])
                    
                    if not forecast_df.empty and 'date' in forecast_df.columns and 'value' in forecast_df.columns:
                        # Create an interactive plot with Plotly
                        fig = px.line(
                            forecast_df, x='date', y='value', 
                            title='Coffee Price Forecast', 
                            labels={'date': 'Month', 'value': 'Price Index'}
                        )
                        
                        fig.update_layout(
                            title_font_size=20,
                            xaxis_title_font_size=14,
                            yaxis_title_font_size=14
                        )
                        
                        # Save the figure if output file is provided
                        if output_file:
                            fig.write_html(output_file)
                            logger.info(f"Saved price trend chart to {output_file}")
                            self.figures['price_trend'] = output_file
                        
                        return output_file
                    
        except Exception as e:
            logger.error(f"Error creating price trend chart: {str(e)}")
            return None
    
    def create_consumption_forecast_chart(self, output_file=None):
        """
        Create a chart showing coffee consumption forecast.
        
        Args:
            output_file (str, optional): Output file path for the chart
            
        Returns:
            str: Path to the saved chart or None if failed
        """
        if not self.trend_results or 'consumption_trends' not in self.trend_results:
            logger.warning("No consumption trend data available for visualization")
            return None
        
        try:
            consumption_data = self.trend_results['consumption_trends']
            
            if 'forecast' in consumption_data and 'next_3_years' in consumption_data['forecast']:
                forecast = consumption_data['forecast']['next_3_years']
                
                # Convert to DataFrame
                forecast_df = pd.DataFrame(forecast)
                
                if not forecast_df.empty and 'year' in forecast_df.columns and 'value' in forecast_df.columns:
                    plt.figure(figsize=(10, 6))
                    
                    sns.barplot(data=forecast_df, x='year', y='value', color='green')
                    plt.title('Coffee Consumption Forecast (Next 3 Years)', fontsize=16)
                    plt.xlabel('Year', fontsize=12)
                    plt.ylabel('Consumption (Tons)', fontsize=12)
                    
                    # Add value labels on top of bars
                    for i, v in enumerate(forecast_df['value']):
                        plt.text(i, v + 5, f"{int(v)}", ha='center')
                    
                    plt.tight_layout()
                    
                    # Save the figure if output file is provided
                    if output_file:
                        plt.savefig(output_file, dpi=300, bbox_inches='tight')
                        logger.info(f"Saved consumption forecast chart to {output_file}")
                        self.figures['consumption_forecast'] = output_file
                    
                    return output_file
                    
        except Exception as e:
            logger.error(f"Error creating consumption forecast chart: {str(e)}")
            return None
    
    def create_hashtag_visualization(self, output_file=None):
        """
        Create a chart visualizing top hashtags from social media.
        
        Args:
            output_file (str, optional): Output file path for the chart
            
        Returns:
            str: Path to the saved chart or None if failed
        """
        if not self.trend_results or 'social_media_trends' not in self.trend_results:
            logger.warning("No social media trend data available for visualization")
            return None
        
        try:
            social_data = self.trend_results['social_media_trends']
            
            if 'hashtags' in social_data and 'top_10' in social_data['hashtags']:
                hashtags = pd.DataFrame(social_data['hashtags']['top_10'])
                
                if not hashtags.empty and 'tag' in hashtags.columns and 'mentions' in hashtags.columns:
                    # Sort by mentions in descending order
                    hashtags = hashtags.sort_values('mentions', ascending=True)
                    
                    plt.figure(figsize=(12, 8))
                    ax = sns.barplot(data=hashtags, y='tag', x='mentions', palette='viridis')
                    
                    # Add value labels
                    for i, v in enumerate(hashtags['mentions']):
                        ax.text(v + 0.1, i, str(v), va='center')
                    
                    plt.title('Top Coffee-Related Hashtags on Social Media', fontsize=16)
                    plt.xlabel('Number of Mentions', fontsize=12)
                    plt.ylabel('Hashtag', fontsize=12)
                    plt.tight_layout()
                    
                    # Save the figure if output file is provided
                    if output_file:
                        plt.savefig(output_file, dpi=300, bbox_inches='tight')
                        logger.info(f"Saved hashtag visualization to {output_file}")
                        self.figures['hashtag_viz'] = output_file
                    
                    return output_file
                    
        except Exception as e:
            logger.error(f"Error creating hashtag visualization: {str(e)}")
            return None
    
    def create_competitor_market_share_chart(self, output_file=None):
        """
        Create a chart showing competitor market share.
        
        Args:
            output_file (str, optional): Output file path for the chart
            
        Returns:
            str: Path to the saved chart or None if failed
        """
        if not self.trend_results or 'competitor_trends' not in self.trend_results:
            logger.warning("No competitor trend data available for visualization")
            return None
        
        try:
            competitor_data = self.trend_results['competitor_trends']
            
            if 'market_share' in competitor_data:
                market_share = pd.DataFrame(competitor_data['market_share'])
                
                if not market_share.empty and 'category' in market_share.columns and 'market_share' in market_share.columns:
                    # Create a pie chart with Plotly
                    fig = px.pie(
                        market_share, 
                        values='market_share',
                        names='category',
                        title='Coffee Shop Market Share by Category',
                        hole=0.4,  # Create a donut chart
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    
                    fig.update_layout(
                        title_font_size=20,
                        legend_title_font_size=14
                    )
                    
                    # Add percentage labels
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    
                    # Save the figure if output file is provided
                    if output_file:
                        fig.write_html(output_file)
                        logger.info(f"Saved competitor market share chart to {output_file}")
                        self.figures['competitor_market_share'] = output_file
                    
                    return output_file
                    
        except Exception as e:
            logger.error(f"Error creating competitor market share chart: {str(e)}")
            return None
    
    def create_price_comparison_by_city_chart(self, output_file=None):
        """
        Create a chart comparing coffee prices across cities.
        
        Args:
            output_file (str, optional): Output file path for the chart
            
        Returns:
            str: Path to the saved chart or None if failed
        """
        if not self.statistical_results or 'pricing_analysis' not in self.statistical_results:
            logger.warning("No pricing analysis data available for visualization")
            return None
        
        try:
            price_data = self.statistical_results['pricing_analysis']
            
            if 'coffee_menu_items' in price_data and 'city_comparison' in price_data['coffee_menu_items']:
                comparison = pd.DataFrame(price_data['coffee_menu_items']['city_comparison'])
                
                if not comparison.empty and 'name' in comparison.columns:
                    # Melt the dataframe to get it in the right format for seaborn
                    cities = [col for col in comparison.columns if col != 'name']
                    melted_df = pd.melt(
                        comparison, 
                        id_vars=['name'], 
                        value_vars=cities,
                        var_name='city', 
                        value_name='price'
                    )
                    
                    # Create a grouped bar chart
                    plt.figure(figsize=(14, 8))
                    ax = sns.barplot(data=melted_df, x='name', y='price', hue='city')
                    
                    plt.title('Coffee Prices by City and Type', fontsize=16)
                    plt.xlabel('Coffee Type', fontsize=12)
                    plt.ylabel('Price (PKR)', fontsize=12)
                    plt.xticks(rotation=45)
                    plt.legend(title='City')
                    plt.tight_layout()
                    
                    # Save the figure if output file is provided
                    if output_file:
                        plt.savefig(output_file, dpi=300, bbox_inches='tight')
                        logger.info(f"Saved price comparison chart to {output_file}")
                        self.figures['price_comparison'] = output_file
                    
                    return output_file
                    
        except Exception as e:
            logger.error(f"Error creating price comparison chart: {str(e)}")
            return None
    
    def create_dashboard(self, output_dir):
        """
        Create a comprehensive dashboard with multiple charts.
        
        Args:
            output_dir (str): Directory to save dashboard files
            
        Returns:
            str: Path to the dashboard HTML file or None if failed
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate all individual charts first
        self.create_city_comparison_chart(os.path.join(output_dir, 'city_comparison.png'))
        self.create_rating_distribution_chart(os.path.join(output_dir, 'rating_distribution.png'))
        self.create_price_trend_chart(os.path.join(output_dir, 'price_trend.html'))
        self.create_consumption_forecast_chart(os.path.join(output_dir, 'consumption_forecast.png'))
        self.create_hashtag_visualization(os.path.join(output_dir, 'hashtag_viz.png'))
        self.create_competitor_market_share_chart(os.path.join(output_dir, 'competitor_market_share.html'))
        self.create_price_comparison_by_city_chart(os.path.join(output_dir, 'price_comparison.png'))
        
        # Create a combined dashboard HTML file
        dashboard_file = os.path.join(output_dir, 'dashboard.html')
        
        try:
            # Create a simple HTML dashboard using the generated images and plotly files
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Coffee Shop Analysis Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        h1 { color: #333; text-align: center; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .full-width { grid-column: span 2; }
        img { max-width: 100%; height: auto; }
        iframe { width: 100%; height: 500px; border: none; }
    </style>
</head>
<body>
    <h1>Coffee Shop Analysis Dashboard</h1>
    <div class="dashboard">
        <div class="card full-width">
            <h2>Coffee Shop Distribution by City</h2>
            <img src="city_comparison.png" alt="City Comparison">
        </div>
        <div class="card">
            <h2>Rating Distribution</h2>
            <img src="rating_distribution.png" alt="Rating Distribution">
        </div>
        <div class="card">
            <h2>Top Coffee-Related Hashtags</h2>
            <img src="hashtag_viz.png" alt="Hashtag Visualization">
        </div>
        <div class="card full-width">
            <h2>Coffee Price Comparison by City</h2>
            <img src="price_comparison.png" alt="Price Comparison">
        </div>
        <div class="card">
            <h2>Consumption Forecast</h2>
            <img src="consumption_forecast.png" alt="Consumption Forecast">
        </div>
        <div class="card">
            <h2>Competitor Market Share</h2>
            <iframe src="competitor_market_share.html"></iframe>
        </div>
        <div class="card full-width">
            <h2>Coffee Price Trends</h2>
            <iframe src="price_trend.html"></iframe>
        </div>
    </div>
</body>
</html>""")
            
            logger.info(f"Created dashboard at {dashboard_file}")
            return dashboard_file
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return None


def create_visualizations(analysis_results=None, timestamp=None):
    """
    Create visualizations based on analysis results.
    
    Args:
        analysis_results: Analysis results (unused in this implementation as we load from files)
        timestamp (str, optional): Timestamp string. If None, current timestamp will be used.
    
    Returns:
        dict: Paths to generated visualizations
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"Creating visualizations for timestamp {timestamp}")
    
    # Set paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    processed_dir = os.path.join(base_dir, PATHS['processed_data'])
    analysis_dir = os.path.join(processed_dir, f"analysis_{timestamp}")
    
    # Check if analysis directory exists, otherwise use latest
    if not os.path.exists(analysis_dir):
        logger.warning(f"Analysis directory {analysis_dir} does not exist")
        analysis_dir = os.path.join(processed_dir, "analysis_latest")
        
        if not os.path.exists(analysis_dir):
            logger.error("No analysis directory found")
            return {}
    
    # Initialize visualizer with analysis directory
    visualizer = CoffeeShopVisualizer(analysis_dir)
    
    # Load analysis results
    if not visualizer.load_analysis_results():
        logger.error("Failed to load analysis results")
        return {}
    
    # Create output directory for visualizations
    output_dir = os.path.join(base_dir, PATHS['processed_data'], f"visualizations_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create dashboard
    dashboard_file = visualizer.create_dashboard(output_dir)
    
    # Save "latest" copy of visualizations
    latest_dir = os.path.join(base_dir, PATHS['processed_data'], "visualizations_latest")
    os.makedirs(latest_dir, exist_ok=True)
    
    if dashboard_file:
        import shutil
        for file in os.listdir(output_dir):
            shutil.copy2(
                os.path.join(output_dir, file),
                os.path.join(latest_dir, file)
            )
    
    return {
        'dashboard': dashboard_file,
        'visualizations_dir': output_dir,
        'figures': visualizer.figures
    }


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create visualizations with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    create_visualizations(None, timestamp)
