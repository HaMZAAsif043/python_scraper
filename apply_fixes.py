"""
Script to update the coffee market data collector with the improved methods.
This script imports the fixed methods and applies them to the main class.
"""

import sys
import os
import re

# Add the parent directory to the path
sys.path.append(os.path.abspath('..'))

# Import the fixed methods
from src.data_collection.fixed_methods import extract_daraz_data, extract_alfatah_data_with_infinite_scroll

# Path to the original file
COFFEE_MARKET_PATH = os.path.join('src', 'data_collection', 'coffee_market.py')

def update_coffee_market_collector():
    """
    Update the coffee market data collector class with the fixed methods.
    
    This function:
    1. Backs up the original file
    2. Replaces the Daraz extraction method
    3. Adds the new Alfatah infinite scrolling method
    4. Updates the collect_data method to use the new Alfatah method
    """
    # Read the original file
    with open(COFFEE_MARKET_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a backup of the original file
    backup_path = COFFEE_MARKET_PATH + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup of original file at {backup_path}")
    
    # Import BeautifulSoup at the top of the file if not already imported
    if "from bs4 import BeautifulSoup" not in content:
        content = re.sub(
            r"import re\n",
            "import re\nfrom bs4 import BeautifulSoup\n",
            content
        )
    
    # Add fixed Daraz method by finding and replacing the original method
    daraz_pattern = r"def extract_daraz_data\(self, max_pages=\d+\):[\s\S]*?logger\.info\(f\"Total extracted \{total_products\} products from Daraz across \{[^}]*\} pages\"\)"
    content = re.sub(
        daraz_pattern,
        extract_daraz_data.__doc__ + extract_daraz_data.__code__.co_consts[0],
        content
    )
    
    # Add Alfatah infinite scrolling method
    # Find the position after the last method before _generate_pagination_url
    alfatah_pos = content.find("def _generate_pagination_url")
    if alfatah_pos != -1:
        # Insert the new method before _generate_pagination_url
        new_alfatah_method = "\n" + extract_alfatah_data_with_infinite_scroll.__doc__ + extract_alfatah_data_with_infinite_scroll.__code__.co_consts[0]
        content = content[:alfatah_pos] + new_alfatah_method + "\n" + content[alfatah_pos:]
    else:
        print("Warning: Could not find a good position to insert the Alfatah infinite scrolling method")
    
    # Update collect_data to use the new Alfatah method
    collect_data_pattern = r"(elif site_name == 'alfatah':.*?\n\s+)(extraction_methods\[site_name\]\(max_pages=\d+\))"
    content = re.sub(
        collect_data_pattern,
        r"\1self.extract_alfatah_data_with_infinite_scroll(max_pages=5)",
        content
    )
    
    # Write the updated content back to the file
    with open(COFFEE_MARKET_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully updated {COFFEE_MARKET_PATH} with fixed methods")
    print("1. Added improved Daraz price extraction with pagination up to 102 pages")
    print("2. Added new Alfatah infinite scrolling implementation")
    print("3. Updated collect_data method to use the new Alfatah method")

if __name__ == "__main__":
    update_coffee_market_collector()
