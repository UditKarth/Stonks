"""
Configuration module for loading environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Alpha Vantage API configuration
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

if not ALPHA_VANTAGE_KEY or ALPHA_VANTAGE_KEY == 'your_api_key_here':
    raise ValueError(
        "Please set your Alpha Vantage API key in the .env file. "
        "Get a free API key from: https://www.alphavantage.co/support/#api-key"
    )
