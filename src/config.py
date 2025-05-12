# Configuration settings for the coffee shop data analysis system

# API keys (replace with your own keys)
API_KEYS = {
    "google_places": "YOUR_GOOGLE_PLACES_API_KEY",
    "twitter": "YOUR_TWITTER_API_KEY",
    "meta_graph": "YOUR_META_GRAPH_API_KEY",
    "foodpanda": "YOUR_FOODPANDA_API_KEY"
}

# Locations to search for coffee shops (modify as needed)
TARGET_LOCATIONS = [
    "Karachi, Pakistan",
    "Lahore, Pakistan",
    "Islamabad, Pakistan",
    "Rawalpindi, Pakistan",
    "Peshawar, Pakistan",
    "Multan, Pakistan",
    "Faisalabad, Pakistan"
]

# Search radius in meters
SEARCH_RADIUS = 5000

# Data sources
DATA_SOURCES = {
    "google_maps": True,
    "facebook": True,
    "twitter": True,
    "food_delivery_apps": True
}

# Data collection frequency (in days)
DATA_COLLECTION_FREQUENCY = 7

# Data storage paths
PATHS = {
    "raw_data": "data/raw",
    "processed_data": "data/processed",
    "reports": "reports"
}

# Report generation settings
REPORTS = {
    "generate_pdf": True,
    "generate_html": True,
    "email_reports": False,
    "email_recipients": ["your-email@example.com"]
}
