import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os

def get_api_config():
    """Get API configuration with detailed error checking"""
    load_dotenv()
    
    api_key = os.getenv('RAPIDAPI_KEY')
    api_host = os.getenv('YT_RAPIDAPI_HOST')
    
    config_status = {
        'is_valid': True,
        'errors': []
    }
    
    if not api_key:
        config_status['is_valid'] = False
        config_status['errors'].append("RAPIDAPI_KEY not found in environment variables")
    
    if not api_host:
        config_status['is_valid'] = False
        config_status['errors'].append("YT_RAPIDAPI_HOST not found in environment variables")
    
    return {
        'key': api_key,
        'host': api_host,
        'status': config_status
    }

def search_youtube(query, country_code="US", language="en"):
    url = "https://yt-api.p.rapidapi.com/search"
    
    querystring = {
        "query": query,
        "geo": country_code,
        "lang": language
    }
    
    # Get API configuration with validation
    api_config = get_api_config()
    
    # Debug information
    st.write("Debug Info:")
    st.write("API Configuration Status:", api_config['status'])
    
    if not api_config['status']['is_valid']:
        for error in api_config['status']['errors']:
            st.error(f"Configuration Error: {error}")
        return None
    
    headers = {
        "x-rapidapi-key": api_config['key'],
        "x-rapidapi-host": api_config['host']
    }
    
    try:
        # Show request details
        st.write("Request Details:")
        st.write(f"API Host: {api_config['host']}")
        st.write(f"Query Parameters: {querystring}")
        
        response = requests.get(url, headers=headers, params=querystring)
        
        # Show response details
        st.write(f"Response Status Code: {response.status_code}")
        st.write("Response Headers:", response.headers)
        
        # Show raw response for debugging
        st.write("Raw Response:", response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
        if response.status_code != 200:
            st.error(f"API Error: Status Code {response.status_code}")
            return None
            
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Request Error: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"JSON Decode Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected Error: {str(e)}")
        return None

def main():
    st.title("YouTube Search App")
    
    # Debug mode toggle
    debug_mode = st.sidebar.checkbox("Debug Mode", value=False)
    
    # Search inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        query = st.text_input("Search query", "")
    with col2:
        country = st.selectbox("Country", 
            ["US", "PL", "DE", "FR", "ES", "IT", "GB", "JP", "KR", "RU"],
            index=0
        )
    with col3:
        language = st.selectbox("Language",
            ["en", "pl", "de", "fr", "es", "it", "ja", "ko", "ru"],
            index=0
        )
    
    if st.button("Search"):
        if query:
            with st.spinner("Searching..."):
                results = search_youtube(query, country, language)
                
                if results and "data" in results:
                    st.success(f"Found {len(results['data'])} results")
                    
                    for item in results["data"]:
                        if item["type"] == "video":
                            # Create columns for layout
                            col1, col2 = st.columns([1, 3])
                            
                            # Display thumbnail
                            with col1:
                                if "thumbnail" in item:
                                    thumbnail_url = item["thumbnail"][0]["url"]
                                    try:
                                        response = requests.get(thumbnail_url)
                                        img = Image.open(BytesIO(response.content))
                                        st.image(img, width=160)
                                    except Exception as e:
                                        if debug_mode:
                                            st.error(f"Thumbnail error: {str(e)}")
                                        else:
                                            st.write("Thumbnail not available")
                            
                            # Display video information
                            with col2:
                                st.markdown(f"### [{item['title']}](https://youtube.com/watch?v={item['videoId']})")
                                st.write(f"Channel: {item.get('channelTitle', 'N/A')}")
                                st.write(f"Views: {item.get('viewCount', 'N/A')}")
                                st.write(f"Duration: {item.get('lengthText', 'N/A')}")
                                if "description" in item:
                                    st.write(f"Description: {item['description'][:200]}...")
                            
                            st.divider()
                            
                            if debug_mode:
                                st.write("Raw item data:", item)
                else:
                    st.error("No results found")
                    if debug_mode:
                        st.write("Raw results:", results)
        else:
            st.warning("Please enter a search query")

if __name__ == "__main__":
    main() 