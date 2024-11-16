import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO

def search_youtube(query, country_code="US", language="en"):
    url = "https://yt-api.p.rapidapi.com/search"
    
    querystring = {
        "query": query,
        "geo": country_code,
        "lang": language
    }
    
    headers = {
        "x-rapidapi-key": "8045e3125cmsh2a1994c6d67e2cap18598bjsnbf7aafc18393",
        "x-rapidapi-host": "yt-api.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

def main():
    st.title("YouTube Search App")
    
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
                
                if "data" in results:
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
                                    except:
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
                else:
                    st.error("No results found")
        else:
            st.warning("Please enter a search query")

if __name__ == "__main__":
    main() 