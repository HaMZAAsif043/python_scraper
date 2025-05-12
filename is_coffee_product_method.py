def _is_coffee_product(self, product_name):
    """
    Check if a product is coffee-related based on its name.
    
    Args:
        product_name (str): Full product name
        
    Returns:
        bool: True if product is coffee-related, False otherwise
    """
    if not product_name or product_name == "Unknown":
        return False
        
    # Convert to lowercase for case-insensitive matching
    name_lower = product_name.lower()
    
    # Coffee-related keywords
    coffee_keywords = [
        'coffee', 'café', 'caffè', 'kaffee', 'nescafe', 'espresso', 'cappuccino', 
        'latte', 'mocha', 'americano', 'java', 'brew', 'arabica', 'robusta', 
        'decaf', 'coffeehouse', 'coffeeshop', 'kopi', 'kahwa', 'قہوہ', 'کافی',
        'barista', 'french press', 'turkish coffee', 'iced coffee', 'coffee bean',
        'cold brew', 'coffee grounds', 'instant coffee'
    ]
    
    # Check if any coffee keyword is in product name
    for keyword in coffee_keywords:
        if keyword in name_lower:
            return True
            
    return False
