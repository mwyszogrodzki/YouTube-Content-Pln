import streamlit as st
from youtube_search import main as search_main
from youtube_downloader import main as downloader_main

def main():
    st.set_page_config(
        page_title="YouTube Tools",
        page_icon="🎥",
        layout="wide"
    )
    
    st.title("YouTube Tools 🎥")
    st.markdown("---")

    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["YouTube Search", "YouTube Downloader"])

    with tab1:
        search_main()

    with tab2:
        downloader_main()

    # Add footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Made with ❤️ using Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 