# Copy all code from youtube_downloader.py
import streamlit as st
import re
import requests
import time
import os
import subprocess
from groq import Groq
from dotenv import load_dotenv

class YouTubeDownloader:
    def __init__(self):
        load_dotenv()
        self.transcripts = []

    # ... (rest of the YouTubeDownloader class)

def main():
    st.title("YouTube to MP3 Downloader & Transcriber")
    
    # Initialize the downloader
    downloader = YouTubeDownloader()
    
    # Get selected videos from session state
    selected_videos = st.session_state.get('selected_videos', [])
    
    # ... (rest of the main function)

if __name__ == "__main__":
    main() 