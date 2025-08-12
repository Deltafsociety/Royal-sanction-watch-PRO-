"""
Configuration file for Royal Sanction Watch
Contains API keys, settings, and configuration options
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # OpenSanctions API Configuration
    OPENSANCTIONS_API_KEY: Optional[str] = os.getenv('OPENSANCTIONS_API_KEY')
    OPENSANCTIONS_BASE_URL: str = os.getenv('OPENSANCTIONS_BASE_URL', 'https://api.opensanctions.org')
    
    # Application Settings
    CACHE_DURATION_HOURS: int = int(os.getenv('CACHE_DURATION_HOURS', '24'))
    SIMILARITY_THRESHOLD: float = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
    MAX_RESULTS_PER_QUERY: int = int(os.getenv('MAX_RESULTS_PER_QUERY', '10'))
    
    # API Rate Limiting
    REQUEST_DELAY_SECONDS: float = float(os.getenv('REQUEST_DELAY_SECONDS', '1.0'))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    
    # File Paths
    CACHE_DIR: str = os.getenv('CACHE_DIR', 'cache')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Default Datasets for OpenSanctions
    DEFAULT_DATASETS = ['sanctions', 'peps', 'default']
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Check if OpenSanctions API key is set (optional but recommended)
        if not cls.OPENSANCTIONS_API_KEY:
            print("Warning: OPENSANCTIONS_API_KEY not set. Some features may be limited.")
        
        # Validate numeric settings
        if cls.CACHE_DURATION_HOURS <= 0:
            errors.append("CACHE_DURATION_HOURS must be positive")
        
        if not 0 <= cls.SIMILARITY_THRESHOLD <= 1:
            errors.append("SIMILARITY_THRESHOLD must be between 0 and 1")
        
        if cls.MAX_RESULTS_PER_QUERY <= 0:
            errors.append("MAX_RESULTS_PER_QUERY must be positive")
        
        if cls.REQUEST_DELAY_SECONDS < 0:
            errors.append("REQUEST_DELAY_SECONDS must be non-negative")
        
        if cls.MAX_RETRIES < 0:
            errors.append("MAX_RETRIES must be non-negative")
        
        if errors:
            print("Configuration errors found:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("Royal Sanction Watch Configuration:")
        print("=" * 40)
        print(f"OpenSanctions API Key: {'Set' if cls.OPENSANCTIONS_API_KEY else 'Not set'}")
        print(f"OpenSanctions Base URL: {cls.OPENSANCTIONS_BASE_URL}")
        print(f"Cache Duration: {cls.CACHE_DURATION_HOURS} hours")
        print(f"Similarity Threshold: {cls.SIMILARITY_THRESHOLD}")
        print(f"Max Results per Query: {cls.MAX_RESULTS_PER_QUERY}")
        print(f"Request Delay: {cls.REQUEST_DELAY_SECONDS} seconds")
        print(f"Max Retries: {cls.MAX_RETRIES}")
        print(f"Cache Directory: {cls.CACHE_DIR}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print()

# Create directories if they don't exist
os.makedirs(Config.CACHE_DIR, exist_ok=True)
os.makedirs(Config.LOG_DIR, exist_ok=True) 