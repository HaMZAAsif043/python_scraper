#!/usr/bin/env python
"""
Script to visualize coffee market data.
Creates visualizations for:
- Price distribution across coffee types and brands
- Brand market share
- Price tier distribution
- Packaging size analysis 
"""

import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project configuration
from src.config import PATHS

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Coffee Market Data Visualization Tool")
    
    parser.add_argument('--input', type=str, default=None,
                        help='Input CSV file (defaults to latest)')
    
    parser.add_argument('--output-dir', type=str, default='reports',
                        help='Output directory for visualizations')
    
    parser.add_argument('--title', type=str, default=None,
                        help='Custom title prefix for plots')
    
    parser.add_argument('--format', choices=['png', 'pdf', 'jpg', 'svg'], default='png',
                        help='Output image format (default: png)')
    
    parser.add_argument('--style', choices=['darkgrid', 'whitegrid', 'dark', 'white', 'ticks'], 
                      default='darkgrid', help='Plot style (default: darkgrid)')
    
    parser.add_argument('--dpi', type=int, default=100,
                       help='DPI for output images (default: 100)')
    
    return parser.parse_args()

def load_data(input_path=None):
    """Load coffee market data from CSV files."""
    
    # If input path is provided, use it directly
    if input_path and os.path.exists(input_path):
        products_df = pd.read_csv(input_path)
        return {
            'products': products_df
        }
    
    # Otherwise use the latest files
    products_path = os.path.join(PATHS['processed_data'], 'coffee_products_latest.csv')
    brands_path = os.path.join(PATHS['processed_data'], 'coffee_brands_latest.csv')
    types_path = os.path.join(PATHS['processed_data'], 'coffee_types_latest.csv')
    packaging_path = os.path.join(PATHS['processed_data'], 'coffee_packaging_latest.csv')
    
    # Load dataframes if files exist
    data = {}
    
    if os.path.exists(products_path):
        data['products'] = pd.read_csv(products_path)
    else:
        print(f"Error: Products file not found at {products_path}")
        sys.exit(1)
        
    if os.path.exists(brands_path):
        data['brands'] = pd.read_csv(brands_path)
    
    if os.path.exists(types_path):
        data['types'] = pd.read_csv(types_path)
        
    if os.path.exists(packaging_path):
        data['packaging'] = pd.read_csv(packaging_path)
    
    return data

def create_visualizations(data, args):
    """Create visualizations from the coffee market data."""
    # Set seaborn style
    sns.set_style(args.style)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Title prefix
    title_prefix = args.title or "Coffee Market Analysis"
    
    # List to store all created visualization paths
    visualization_paths = []
    
    # 1. Price Distribution by Coffee Type
    if 'products' in data and 'type' in data['products'].columns:
        plt.figure(figsize=(12, 6))
        ax = sns.boxplot(x='type', y='price', data=data['products'])
        ax.set_title(f"{title_prefix}: Price Distribution by Coffee Type")
        ax.set_xlabel("Coffee Type")
        ax.set_ylabel("Price (PKR)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(args.output_dir, f"price_by_type_{timestamp}.{args.format}")
        plt.savefig(output_path, dpi=args.dpi)
        visualization_paths.append(output_path)
        plt.close()
        
    # 2. Brand Market Share (Top 10)
    if 'brands' in data and 'product_count' in data['brands'].columns:
        plt.figure(figsize=(12, 6))
        top_brands = data['brands'].nlargest(10, 'product_count')
        ax = sns.barplot(x='brand', y='product_count', data=top_brands)
        ax.set_title(f"{title_prefix}: Top 10 Coffee Brands by Market Share")
        ax.set_xlabel("Brand")
        ax.set_ylabel("Number of Products")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(args.output_dir, f"brand_market_share_{timestamp}.{args.format}")
        plt.savefig(output_path, dpi=args.dpi)
        visualization_paths.append(output_path)
        plt.close()
    
    # 3. Price Tier Distribution
    if 'products' in data and 'price_tier' in data['products'].columns:
        plt.figure(figsize=(10, 6))
        tier_counts = data['products']['price_tier'].value_counts()
        
        colors = {
            'low': '#66c2a5',     # Soft green for economy
            'mid': '#fc8d62',     # Orange for mid-range
            'premium': '#8da0cb'  # Blue for premium
        }
          # Create a color map for the tiers
        tier_colors = [colors.get(tier, '#cccccc') for tier in tier_counts.index]
        
        # Fix the FutureWarning by using hue parameter
        tier_df = pd.DataFrame({
            'tier': tier_counts.index,
            'count': tier_counts.values
        })
        ax = sns.barplot(x='tier', y='count', data=tier_df, hue='tier', palette=tier_colors, legend=False)
        
        ax.set_title(f"{title_prefix}: Price Tier Distribution")
        ax.set_xlabel("Price Tier")
        ax.set_ylabel("Number of Products")
        
        # Add value labels on top of each bar
        for i, v in enumerate(tier_counts.values):
            ax.text(i, v + 0.5, str(v), ha='center')
        
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(args.output_dir, f"price_tiers_{timestamp}.{args.format}")
        plt.savefig(output_path, dpi=args.dpi)
        visualization_paths.append(output_path)
        plt.close()
    
    # 4. Average Price by Brand (Top 10)
    if 'brands' in data and 'avg_price' in data['brands'].columns:
        plt.figure(figsize=(12, 6))
        top_brands_price = data['brands'].nlargest(10, 'avg_price')
        ax = sns.barplot(x='brand', y='avg_price', data=top_brands_price)
        ax.set_title(f"{title_prefix}: Top 10 Coffee Brands by Average Price")
        ax.set_xlabel("Brand")
        ax.set_ylabel("Average Price (PKR)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(args.output_dir, f"brand_avg_price_{timestamp}.{args.format}")
        plt.savefig(output_path, dpi=args.dpi)
        visualization_paths.append(output_path)
        plt.close()
    
    # 5. Source Website Distribution
    if 'products' in data and 'source' in data['products'].columns:
        plt.figure(figsize=(10, 6))
        source_counts = data['products']['source'].value_counts()
        ax = sns.barplot(x=source_counts.index, y=source_counts.values)
        ax.set_title(f"{title_prefix}: Data Source Distribution")
        ax.set_xlabel("Website Source")
        ax.set_ylabel("Number of Products")
        plt.xticks(rotation=45)
        
        # Add value labels on top of each bar
        for i, v in enumerate(source_counts.values):
            ax.text(i, v + 0.5, str(v), ha='center')
            
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(args.output_dir, f"source_distribution_{timestamp}.{args.format}")
        plt.savefig(output_path, dpi=args.dpi)
        visualization_paths.append(output_path)
        plt.close()
    
    # Create a summary file with links to all visualizations
    summary_path = os.path.join(args.output_dir, f"visualization_summary_{timestamp}.html")
    with open(summary_path, 'w') as f:
        f.write(f"<html><head><title>{title_prefix} Visualizations</title></head><body>\n")
        f.write(f"<h1>{title_prefix} Visualizations</h1>\n")
        f.write(f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n")
        f.write("<ul>\n")
        
        for path in visualization_paths:
            filename = os.path.basename(path)
            f.write(f'<li><a href="{filename}">{filename}</a></li>\n')
        
        f.write("</ul>\n")
        f.write("</body></html>\n")
    
    print(f"Visualizations created: {len(visualization_paths)}")
    print(f"Summary HTML: {summary_path}")
    
    return {
        'visualization_paths': visualization_paths,
        'summary_path': summary_path
    }

def main():
    """Main function to run the coffee market data visualization."""
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Load the data
        print("Loading coffee market data...")
        data = load_data(args.input)
        
        # Create visualizations
        print("Creating visualizations...")
        result = create_visualizations(data, args)
        
        print(f"Done! Created {len(result['visualization_paths'])} visualizations.")
        print(f"Summary available at: {result['summary_path']}")
        
        return 0
        
    except Exception as e:
        print(f"Error during visualization: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
