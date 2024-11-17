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
        self.current_transcript = ""

    def extract_video_id(self, url):
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def check_conversion_status(self, video_id):
        """Check conversion status from API"""
        try:
            # Try to get API keys from Streamlit secrets first
            headers = {
                'x-rapidapi-key': st.secrets.api_credentials.rapidapi_key,
                'x-rapidapi-host': st.secrets.api_credentials.rapidapi_host
            }
        except:
            # Fall back to environment variables
            headers = {
                'x-rapidapi-key': os.getenv('RAPIDAPI_KEY'),
                'x-rapidapi-host': os.getenv('RAPIDAPI_HOST')
            }
        
        with st.spinner('Converting video...'):
            while True:
                try:
                    response = requests.get(
                        f"https://youtube-mp36.p.rapidapi.com/dl?id={video_id}",
                        headers=headers
                    )
                    data = response.json()
                    
                    if data.get('status') == 'ok':
                        return data.get('link')
                        
                    time.sleep(2)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    return None

    def download_and_process_file(self, url):
        """Download MP3 and process it"""
        try:
            with st.spinner('Downloading and processing audio...'):
                # Download the MP3 file
                response = requests.get(url)
                mp3_path = "audio_file.mp3"
                ogg_path = "audio.ogg"
                
                with open(mp3_path, "wb") as f:
                    f.write(response.content)
                
                # Convert to OGG using ffmpeg
                subprocess.run([
                    'ffmpeg', '-i', mp3_path,
                    '-vn', '-map_metadata', '-1',
                    '-ac', '1', '-c:a', 'libopus',
                    '-b:a', '12k', '-application', 'voip',
                    ogg_path
                ], check=True)
                
                # Transcribe using Groq
                try:
                    client = Groq(
                        api_key=st.secrets.api_credentials.groq_api_key
                    )
                except:
                    client = Groq(
                        api_key=os.getenv('GROQ_API_KEY')
                    )
                
                with open(ogg_path, "rb") as file:
                    transcription = client.audio.transcriptions.create(
                        file=(ogg_path, file.read()),
                        model="whisper-large-v3-turbo",
                        response_format="verbose_json",
                    )
                
                # Clean up temporary files
                os.remove(mp3_path)
                os.remove(ogg_path)
                
                return transcription.text
                
        except Exception as e:
            st.error(f"Processing error: {str(e)}")
            return None

def main():
    st.title("YouTube to MP3 Downloader & Transcriber")
    
    # Initialize the downloader
    downloader = YouTubeDownloader()
    
    # URL input
    url = st.text_input("Enter YouTube URL:")
    
    if st.button("Convert to MP3 and Transcribe"):
        if url:
            video_id = downloader.extract_video_id(url)
            
            if not video_id:
                st.error("Invalid YouTube URL")
            else:
                # Get download link
                download_link = downloader.check_conversion_status(video_id)
                
                if download_link:
                    # Process the file and get transcript
                    transcript = downloader.download_and_process_file(download_link)
                    
                    if transcript:
                        st.success("Processing complete!")
                        
                        # Display transcript
                        st.subheader("Transcript:")
                        st.text_area("", transcript, height=300)
                        
                        # Download button for transcript
                        st.download_button(
                            label="Download Transcript",
                            data=transcript,
                            file_name="transcript.txt",
                            mime="text/plain"
                        )
        else:
            st.warning("Please enter a YouTube URL")

if __name__ == "__main__":
    main() 