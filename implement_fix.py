"""
Script to implement the fixed Foodpanda extractor method into the coffee_market.py file
"""

import re
import os
import traceback
from pathlib import Path

def update_file():    # Path to the coffee market scraper
    file_path = r"c:\Users\MADIHA\Desktop\python automation\src\data_collection\coffee_market.py"
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Read the fixed method
    with open(r"c:\Users\MADIHA\Desktop\python automation\foodpanda_fix.py", 'r', encoding='utf-8') as f:
        fixed_method = f.read()
    
    # Extract only the method content (without the docstring header)
    fixed_method = fixed_method.split('"""', 2)[2].strip()
    
    # Pattern to match the existing extract_foodpanda_data method
    pattern = r'def extract_foodpanda_data\(self,.*?(?=def|$)'
    
    # Use re.DOTALL to match across multiple lines
    updated_content = re.sub(pattern, fixed_method, content, flags=re.DOTALL)
    
    # Make a backup of the original file
    backup_path = file_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup at {backup_path}")
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Updated {file_path} with the fixed extract_foodpanda_data method")
    
    return True

if __name__ == "__main__":
    try:
        result = update_file()
        print("Success!" if result else "Failed to update file")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
