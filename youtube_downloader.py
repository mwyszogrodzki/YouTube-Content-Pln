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

    def add_transcript(self, url, title, transcript):
        """Add a transcript to the collection"""
        self.transcripts.append({
            'url': url,
            'title': title,
            'transcript': transcript,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

def main():
    st.title("YouTube to MP3 Downloader & Transcriber")
    
    # Initialize the downloader
    downloader = YouTubeDownloader()
    
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
    
    for video in selected_videos:
        st.subheader(f"Processing: {video['title']}")
        url = video['url']
        
        video_id = downloader.extract_video_id(url)
        if not video_id:
            st.error(f"Invalid YouTube URL: {url}")
            continue
            
        # Get download link
        download_link = downloader.check_conversion_status(video_id)
        
        if download_link:
            # Process the file and get transcript
            transcript = downloader.download_and_process_file(download_link)
            
            if transcript:
                all_transcripts.append({
                    'title': video['title'],
                    'url': url,
                    'transcript': transcript
                })
                st.success(f"Successfully processed: {video['title']}")
    
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
                st.experimental_rerun()

if __name__ == "__main__":
    main() 