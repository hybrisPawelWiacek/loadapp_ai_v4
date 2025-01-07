import requests
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import pickle
from pathlib import Path

# Configuration
API_URL = "http://127.0.0.1:5001"
API_BASE_URL = API_URL
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'http://localhost:8501'
}

# Cache paths
CACHE_DIR = Path("cache")
BUSINESS_CACHE_FILE = CACHE_DIR / "business_entities.pkl"
ROUTE_HISTORY_FILE = CACHE_DIR / "route_history.pkl"

def init_cache():
    """Initialize cache directory and files."""
    CACHE_DIR.mkdir(exist_ok=True)
    for cache_file in [BUSINESS_CACHE_FILE, ROUTE_HISTORY_FILE]:
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                st.error(f"Error cleaning cache: {e}")

def api_request(endpoint: str, method: str = "GET", data: Dict = None, timeout: int = 10) -> Optional[Dict]:
    """Make an API request with error handling."""
    try:
        url = f"{API_URL}{endpoint}"
        
        # Default timeouts for different operations
        if timeout is None:
            if method == "POST":
                timeout = 30  # Longer default timeout for POST operations
            else:
                timeout = 10  # Default timeout for other operations
        
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS, timeout=timeout)
            if response.status_code == 204:
                return None
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code in [200, 201]:
            return response.json()
        else:
            try:
                error_data = response.json()
                error_message = error_data.get('error', response.text)
                st.error(f"API request failed: {error_message}")
            except:
                st.error(f"API request failed: {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error(f"API request timed out after {timeout} seconds")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Unable to connect to the API server")
        return None
    except Exception as e:
        st.error(f"API request error: {str(e)}")
        return None

def fetch_transport_types() -> List[tuple]:
    """Fetch available transport types from the API."""
    response = api_request("/api/transport/types")
    if response:
        return [(t["id"], t["name"]) for t in response]
    return []

def fetch_business_entities() -> List[Dict]:
    """Fetch available business entities with caching."""
    try:
        response = api_request("/api/business")
        if response:
            # Cache the results
            CACHE_DIR.mkdir(exist_ok=True)
            with open(BUSINESS_CACHE_FILE, 'wb') as f:
                pickle.dump(response, f)
            return response
        
        # Try to load from cache if API fails
        if BUSINESS_CACHE_FILE.exists():
            with open(BUSINESS_CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        return []
    except Exception as e:
        st.error(f"Error fetching business entities: {str(e)}")
        # Try to load from cache
        if BUSINESS_CACHE_FILE.exists():
            with open(BUSINESS_CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        return []

def save_to_history(route_data: Dict[str, Any], costs: Dict[str, Any], offer: Dict[str, Any]):
    """Save route, costs, and offer to history."""
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'route': route_data,
        'costs': costs,
        'offer': offer
    }
    
    # Load existing history
    history = []
    if ROUTE_HISTORY_FILE.exists():
        with open(ROUTE_HISTORY_FILE, 'rb') as f:
            history = pickle.load(f)
    
    # Add new entry and save
    history.append(history_entry)
    with open(ROUTE_HISTORY_FILE, 'wb') as f:
        pickle.dump(history, f)

def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"€{amount:.2f}"

def format_distance(km: float) -> str:
    """Format distance in kilometers."""
    return f"{km:.1f} km"

def format_duration(hours: float) -> str:
    """Format duration in hours."""
    return f"{hours:.1f}h"

def validate_address(address: str) -> bool:
    """Basic address validation.
    Validates that the address has at least a city and country separated by comma.
    Handles whitespace and case variations."""
    if not address:
        return False
    # Split by comma and clean up each part
    parts = [p.strip().lower() for p in address.split(',')]
    # Remove empty parts
    parts = [p for p in parts if p]
    # Check if we have at least 2 non-empty parts
    return len(parts) >= 2

def cleanup_resources():
    """Cleanup function to be called on app shutdown."""
    try:
        for cache_file in [BUSINESS_CACHE_FILE, ROUTE_HISTORY_FILE]:
            if cache_file.exists():
                cache_file.unlink()
    except Exception as e:
        st.error(f"Error cleaning up resources: {e}") 