import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Hello World App",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Hello World Application")

# Define the API URL
API_URL = "http://127.0.0.1:5000"  # Using 127.0.0.1 instead of localhost

def get_hello_message():
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'http://localhost:8501'  # Add explicit origin
    }
    
    try:
        st.write("Attempting to connect to backend...")
        endpoint = f"{API_URL}/api/hello"
        st.write(f"Requesting: {endpoint}")
        
        response = requests.get(
            endpoint,
            headers=headers,
            timeout=5  # Add timeout
        )
        
        st.write(f"Response status code: {response.status_code}")
        st.write(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                st.success(data["message"])
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON response: {str(e)}")
                st.write(f"Raw response: {response.text}")
        else:
            st.error(f"Failed to get message from backend. Status code: {response.status_code}")
            st.write(f"Response content: {response.text}")
            
            # Additional debugging information
            st.write("Debug Information:")
            st.write(f"Request URL: {endpoint}")
            st.write(f"Request Headers: {headers}")
            
    except requests.exceptions.ConnectionError as e:
        st.error(f"Cannot connect to backend server. Please ensure it's running on {API_URL}\nError: {str(e)}")
    except requests.exceptions.Timeout:
        st.error(f"Request timed out while connecting to {API_URL}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.write(f"Error type: {type(e).__name__}")

if st.button("Get Hello Message"):
    get_hello_message()
