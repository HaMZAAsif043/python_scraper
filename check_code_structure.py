"""
Check the coffee market code structure
"""

import sys
import os
import importlib.util

def check_code_structure():
    # Try to load the module from file path
    try:
        spec = importlib.util.spec_from_file_location(
            "coffee_market", 
            "src/data_collection/coffee_market.py"
        )
        coffee_market = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(coffee_market)
        
        # Check if the class exists
        if hasattr(coffee_market, 'CoffeeMarketDataCollector'):
            print("CoffeeMarketDataCollector class found")
            
            # Get all methods of the class
            collector_class = coffee_market.CoffeeMarketDataCollector
            methods = [method for method in dir(collector_class) if callable(getattr(collector_class, method))]
            
            print("\nClass methods:")
            for method in sorted(methods):
                if not method.startswith('__'):  # Skip built-in methods
                    print(f"- {method}")
                    
            # Check for specific methods
            target_methods = [
                '_extract_brand',
                '_extract_coffee_type',
                '_extract_packaging_info',
                '_get_price_tier',
                '_update_aggregated_data',
                '_is_coffee_product',
                'extract_foodpanda_data'
            ]
            
            print("\nChecking for target methods:")
            for method in target_methods:
                if method in methods:
                    print(f"- {method}: FOUND")
                else:
                    print(f"- {method}: MISSING")
        else:
            print("CoffeeMarketDataCollector class NOT found")
    
    except Exception as e:
        print(f"Error analyzing code: {e}")

if __name__ == "__main__":
    check_code_structure()
