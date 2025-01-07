import requests
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
import json
import pickle
from pathlib import Path
import traceback

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

def api_request(endpoint: str, method: str = "GET", data: Dict = None, _debug: bool = False) -> Optional[Dict]:
    """Make an API request with optional debug logging."""
    try:
        url = f"http://localhost:5001{endpoint}"
        if _debug:
            print(f"[DEBUG] Making {method} request to {url}")
            if data:
                print(f"[DEBUG] Request data: {data}")
                
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        if _debug:
            print(f"[DEBUG] Response status code: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            try:
                print(f"[DEBUG] Response content: {response.content.decode()}")
            except:
                print(f"[DEBUG] Raw response content: {response.content}")
                
        if response.status_code == 404:
            if _debug:
                print("[DEBUG] Resource not found")
            return None
            
        if response.status_code >= 400:
            if _debug:
                print(f"[DEBUG] Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                if _debug:
                    print(f"[DEBUG] Error response: {error_data}")
                return {"error": error_data.get("detail", str(error_data))}
            except:
                if _debug:
                    print("[DEBUG] Could not parse error response as JSON")
                return {"error": response.text or f"Request failed with status {response.status_code}"}
                
        try:
            return response.json()
        except ValueError as e:
            if _debug:
                print(f"[DEBUG] Failed to parse response as JSON: {str(e)}")
            return None
            
    except requests.exceptions.RequestException as e:
        if _debug:
            print(f"[DEBUG] Request failed: {str(e)}")
        return None
    except Exception as e:
        if _debug:
            print(f"[DEBUG] Unexpected error: {str(e)}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
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

def format_currency(amount: Union[str, float, Decimal]) -> str:
    """Format amount as currency.
    
    Args:
        amount: Amount to format (can be string, float, or Decimal)
    Returns:
        Formatted currency string
    """
    if isinstance(amount, str):
        amount = float(amount)
    elif isinstance(amount, Decimal):
        amount = float(amount)
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