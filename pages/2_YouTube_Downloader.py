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
        self.status_placeholder = None

    def update_status(self, message, is_error=False):
        """Update status message in the UI"""
        if is_error:
            self.status_placeholder.error(message)
        else:
            self.status_placeholder.info(message)

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
        
        self.update_status("Starting video conversion...")
        attempts = 0
        max_attempts = 30  # Maximum number of attempts (60 seconds)
        
        while attempts < max_attempts:
            try:
                response = requests.get(
                    f"https://youtube-mp36.p.rapidapi.com/dl?id={video_id}",
                    headers=headers
                )
                data = response.json()
                
                if data.get('status') == 'ok':
                    self.update_status("Video conversion completed successfully!")
                    return data.get('link')
                
                self.update_status(f"Converting... Attempt {attempts + 1}/{max_attempts}")
                time.sleep(2)
                attempts += 1
                
            except Exception as e:
                self.update_status(f"Conversion error: {str(e)}", is_error=True)
                return None
        
        self.update_status("Conversion timed out", is_error=True)
        return None

    def download_and_process_file(self, url):
        """Download MP3 and process it"""
        try:
            # Download the MP3 file
            self.update_status("Downloading MP3 file...")
            response = requests.get(url)
            mp3_path = "audio_file.mp3"
            ogg_path = "audio.ogg"
            
            with open(mp3_path, "wb") as f:
                f.write(response.content)
            
            # Convert to OGG
            self.update_status("Converting audio format...")
            try:
                subprocess.run([
                    'ffmpeg', '-i', mp3_path,
                    '-vn', '-map_metadata', '-1',
                    '-ac', '1', '-c:a', 'libopus',
                    '-b:a', '12k', '-application', 'voip',
                    ogg_path
                ], check=True)
            except subprocess.CalledProcessError as e:
                self.update_status(f"FFmpeg conversion error: {str(e)}", is_error=True)
                return None
            
            # Transcribe using Groq
            self.update_status("Initializing transcription service...")
            try:
                client = Groq(
                    api_key=st.secrets.api_credentials.groq_api_key
                )
            except:
                client = Groq(
                    api_key=os.getenv('GROQ_API_KEY')
                )
            
            self.update_status("Starting transcription...")
            with open(ogg_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(ogg_path, file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                )
            
            # Clean up
            self.update_status("Cleaning up temporary files...")
            os.remove(mp3_path)
            os.remove(ogg_path)
            
            self.update_status("Transcription completed successfully!")
            return transcription.text
                
        except Exception as e:
            self.update_status(f"Processing error: {str(e)}", is_error=True)
            return None

def main():
    st.title("YouTube to MP3 Downloader & Transcriber")
    
    # Initialize the downloader
    downloader = YouTubeDownloader()
    
    # Create a placeholder for status messages
    downloader.status_placeholder = st.empty()
    
    # Get selected videos from session state
    selected_videos = st.session_state.get('selected_videos', [])
    
    if not selected_videos:
        # Show manual URL input if no videos were selected
        url = st.text_input("Enter YouTube URL:")
        title = "Manual Entry"
        if url:
            selected_videos = [{'url': url, 'title': title}]
    else:
        st.write(f"Processing {len(selected_videos)} selected videos")
    
    # Process all videos
    all_transcripts = []
    
    for i, video in enumerate(selected_videos, 1):
        st.subheader(f"Processing video {i}/{len(selected_videos)}: {video['title']}")
        progress_bar = st.progress(0)
        url = video['url']
        
        # Extract video ID
        progress_bar.progress(10)
        video_id = downloader.extract_video_id(url)
        if not video_id:
            downloader.update_status(f"Invalid YouTube URL: {url}", is_error=True)
            continue
        
        # Get download link
        progress_bar.progress(30)
        download_link = downloader.check_conversion_status(video_id)
        
        if download_link:
            # Process the file and get transcript
            progress_bar.progress(60)
            transcript = downloader.download_and_process_file(download_link)
            
            if transcript:
                progress_bar.progress(100)
                all_transcripts.append({
                    'title': video['title'],
                    'url': url,
                    'transcript': transcript
                })
                st.success(f"Successfully processed: {video['title']}")
            else:
                progress_bar.progress(0)
        else:
            progress_bar.progress(0)
    
    # If we have any transcripts, combine them and offer download
    if all_transcripts:
        st.success("All processing complete!")
        
        # Combine transcripts into one document
        combined_text = ""
        for t in all_transcripts:
            combined_text += f"\n\n{'='*50}\n"
            combined_text += f"Title: {t['title']}\n"
            combined_text += f"URL: {t['url']}\n"
            combined_text += f"{'='*50}\n\n"
            combined_text += t['transcript']
        
        # Display combined transcript
        st.subheader("Combined Transcript:")
        st.text_area("", combined_text, height=300)
        
        # Download button for combined transcript
        st.download_button(
            label="Download Combined Transcript",
            data=combined_text,
            file_name="combined_transcripts.txt",
            mime="text/plain"
        )
        
        # Clear selected videos after processing
        if 'selected_videos' in st.session_state:
            if st.button("Clear Selected Videos"):
                st.session_state.selected_videos = []
                st.rerun()

if __name__ == "__main__":
    main() 