def _generate_pagination_url(self, base_url, page_number, site_name):
    """
    Generate a pagination URL for a specific site.
    
    Args:
        base_url (str): The base search URL
        page_number (int): The page number to generate URL for
        site_name (str): The name of the site to generate URL for
        
    Returns:
        str: The URL for the specified page
    """        
    # Different sites have different pagination URL structures
    if site_name == 'naheed':
        # Naheed uses the 'p' parameter
        if '?' in base_url:
            return f"{base_url}&p={page_number}"
        else:
            return f"{base_url}?p={page_number}"
    elif site_name == 'alibaba':
        # Alibaba might use a different structure depending on the URL format
        if '/page/' in base_url:
            return re.sub(r'/page/\d+', f'/page/{page_number}', base_url)
        elif 'page=' in base_url:
            return re.sub(r'page=\d+', f'page={page_number}', base_url)
        else:
            # Alibaba often uses a different pagination structure like /page/2
            return f"{base_url}/page/{page_number}"
    else:
        # Default pagination pattern (daraz, alfatah, metro, foodpanda use similar patterns)
        if 'page=' in base_url:
            return re.sub(r'page=\d+', f'page={page_number}', base_url)
        elif '?' in base_url:
            return f"{base_url}&page={page_number}"
        else:
            return f"{base_url}?page={page_number}"
