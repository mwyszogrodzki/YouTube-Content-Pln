import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os

def get_api_config():
    """Get API configuration with detailed error checking"""
    load_dotenv()  # Load environment variables as fallback
    
    # Try to get API keys from Streamlit secrets first, then fall back to env vars
    try:
        api_key = st.secrets.api_credentials.rapidapi_key
        api_host = st.secrets.api_credentials.yt_rapidapi_host
    except:
        api_key = os.getenv('RAPIDAPI_KEY')
        api_host = os.getenv('YT_RAPIDAPI_HOST')
    
    if not api_key or not api_host:
        st.error("API configuration error. Please check your credentials.")
        return None
        
    return {
        'key': api_key,
        'host': api_host
    }

def search_youtube(query, country_code="US", language="en"):
    url = "https://yt-api.p.rapidapi.com/search"
    
    querystring = {
        "query": query,
        "geo": country_code,
        "lang": language
    }
    
    # Get API configuration
    api_config = get_api_config()
    if not api_config:
        return None
    
    headers = {
        "x-rapidapi-key": api_config['key'],
        "x-rapidapi-host": api_config['host']
    }
    
    try:
        with st.spinner('Searching...'):
            response = requests.get(url, headers=headers, params=querystring)
            
            if response.status_code != 200:
                st.error("Failed to fetch search results")
                return None
                
            return response.json()
            
    except Exception as e:
        st.error("Error occurred while searching")
        return None

def check_auth():
    """Check if user is authenticated"""
    if "password_correct" not in st.session_state:
        st.error("Please log in first")
        st.stop()
    if not st.session_state["password_correct"]:
        st.error("Please log in first")
        st.stop()

def main():
    # Check authentication first
    check_auth()
    
    st.title("YouTube Search App")
    
    # Create/access session state for selected videos and search results
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""
    if 'last_country' not in st.session_state:
        st.session_state.last_country = "US"
    if 'last_language' not in st.session_state:
        st.session_state.last_language = "en"
    
    # Show selected videos count and list in sidebar
    st.sidebar.write(f"Selected Videos: {len(st.session_state.selected_videos)}")
    if st.session_state.selected_videos:
        st.sidebar.write("Selected:")
        for video in st.session_state.selected_videos:
            st.sidebar.write(f"- {video['title'][:50]}...")
    
    if st.sidebar.button("Process Selected Videos"):
        st.switch_page("pages/2_YouTube_Downloader.py")
    
    # Search inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        query = st.text_input("Search query", value=st.session_state.last_query)
    with col2:
        country = st.selectbox("Country", 
            ["US", "PL", "DE", "FR", "ES", "IT", "GB", "JP", "KR", "RU"],
            index=["US", "PL", "DE", "FR", "ES", "IT", "GB", "JP", "KR", "RU"].index(st.session_state.last_country)
        )
    with col3:
        language = st.selectbox("Language",
            ["en", "pl", "de", "fr", "es", "it", "ja", "ko", "ru"],
            index=["en", "pl", "de", "fr", "es", "it", "ja", "ko", "ru"].index(st.session_state.last_language)
        )
    
    def handle_selection(video_data):
        if video_data['url'] in [v['url'] for v in st.session_state.selected_videos]:
            st.session_state.selected_videos = [
                v for v in st.session_state.selected_videos 
                if v['url'] != video_data['url']
            ]
        else:
            st.session_state.selected_videos.append(video_data)
    
    # Search button or results already exist
    if st.button("Search") or st.session_state.search_results:
        if query and (query != st.session_state.last_query or 
                     country != st.session_state.last_country or 
                     language != st.session_state.last_language):
            st.session_state.search_results = search_youtube(query, country, language)
            st.session_state.last_query = query
            st.session_state.last_country = country
            st.session_state.last_language = language
        
        results = st.session_state.search_results
        if results and "data" in results:
            st.success(f"Found {len(results['data'])} results")
            
            for item in results["data"]:
                if item["type"] == "video":
                    # Create columns for layout
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    # Display thumbnail
                    with col1:
                        if "thumbnail" in item:
                            thumbnail_url = item["thumbnail"][0]["url"]
                            try:
                                response = requests.get(thumbnail_url)
                                img = Image.open(BytesIO(response.content))
                                st.image(img, width=160)
                            except:
                                st.write("Thumbnail not available")
                    
                    # Display video information
                    with col2:
                        video_url = f"https://youtube.com/watch?v={item['videoId']}"
                        st.markdown(f"### [{item['title']}]({video_url})")
                        st.write(f"Channel: {item.get('channelTitle', 'N/A')}")
                        st.write(f"Views: {item.get('viewCount', 'N/A')}")
                        st.write(f"Duration: {item.get('lengthText', 'N/A')}")
                        if "description" in item:
                            st.write(f"Description: {item['description'][:200]}...")
                    
                    # Add select button
                    with col3:
                        video_data = {
                            'url': video_url,
                            'title': item['title']
                        }
                        is_selected = video_url in [v['url'] for v in st.session_state.selected_videos]
                        button_label = 'Deselect' if is_selected else 'Select for Transcription'
                        if st.button(button_label, key=f"btn_{item['videoId']}"):
                            handle_selection(video_data)
                            st.rerun()
                    
                    st.divider()
        else:
            if query:
                st.error("No results found")
    else:
        st.warning("Please enter a search query")

if __name__ == "__main__":
    main() 