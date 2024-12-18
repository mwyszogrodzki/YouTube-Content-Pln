# Copy all code from youtube_downloader.py
import streamlit as st
import re
import requests
import time
import os
import subprocess
from groq import Groq
from dotenv import load_dotenv
import json

class YouTubeDownloader:
    def __init__(self):
        load_dotenv()
        self.transcripts = []
        self.status_placeholder = None
        self.kb_api_endpoint = "http://37.27.34.28/v1/workflows/run"

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
        max_attempts = 15  # Reduced from 30 to 15 attempts
        
        while attempts < max_attempts:
            try:
                response = requests.get(
                    f"https://youtube-mp36.p.rapidapi.com/dl?id={video_id}",
                    headers=headers
                )
                data = response.json()
                
                # Check for different status responses
                if data.get('status') == 'ok':
                    self.update_status("Video conversion completed successfully!")
                    return data.get('link')
                elif data.get('status') == 'processing':
                    self.update_status(f"Video is being converted... (Attempt {attempts + 1}/{max_attempts})")
                elif data.get('status') == 'fail':
                    self.update_status(f"Conversion failed: {data.get('msg', 'Unknown error')}", is_error=True)
                    return None
                
                time.sleep(4)  # Increased delay between attempts to 4 seconds
                attempts += 1
                
            except Exception as e:
                self.update_status(f"Conversion error: {str(e)}", is_error=True)
                return None
        
        self.update_status("Conversion timed out - video might be too long or unavailable", is_error=True)
        return None

    def check_ffmpeg(self):
        """Check if FFmpeg is installed and accessible"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return True
        except FileNotFoundError:
            self.update_status("""
            FFmpeg is not installed or not found in PATH. 
            
            To install FFmpeg:
            - On Ubuntu/Debian: sudo apt-get install ffmpeg
            - On macOS: brew install ffmpeg
            - On Windows: Download from https://www.ffmpeg.org/download.html
            
            After installing, please restart the application.
            """, is_error=True)
            return False

    def download_and_process_file(self, url):
        """Download MP3 and process it"""
        try:
            # Check FFmpeg first
            if not self.check_ffmpeg():
                return None

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
                # Add full path for ffmpeg in Streamlit Cloud
                ffmpeg_cmd = 'ffmpeg'
                if os.path.exists('/usr/bin/ffmpeg'):
                    ffmpeg_cmd = '/usr/bin/ffmpeg'
                elif os.path.exists('/usr/local/bin/ffmpeg'):
                    ffmpeg_cmd = '/usr/local/bin/ffmpeg'
                
                subprocess.run([
                    ffmpeg_cmd, '-i', mp3_path,
                    '-vn', '-map_metadata', '-1',
                    '-ac', '1', '-c:a', 'libopus',
                    '-b:a', '12k', '-application', 'voip',
                    ogg_path
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                self.update_status(f"FFmpeg conversion error: {e.stderr.decode()}", is_error=True)
                return None
            except Exception as e:
                self.update_status(f"FFmpeg error: {str(e)}", is_error=True)
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

    def generate_knowledge_base(self, keyword, language_code, combined_transcription):
        """Generate knowledge base from transcriptions"""
        self.update_status("Initializing knowledge base generation...")
        
        # Convert language code to full name
        language_map = {
            'en': 'english',
            'pl': 'polish',
            'de': 'german',
            'fr': 'french',
            'es': 'spanish',
            'it': 'italian',
            'ja': 'japanese',
            'ko': 'korean',
            'ru': 'russian'
        }
        
        language = language_map.get(language_code, 'english')
        
        try:
            # Get API key from secrets or environment variables
            try:
                api_key = st.secrets.api_credentials.knowledge_base_api_key
            except:
                api_key = os.getenv('KNOWLEDGE_BASE_API_KEY')
            
            if not api_key:
                self.update_status("API key not found", is_error=True)
                return None
                
            self.update_status(f"Using API key: {api_key[:8]}...")
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Match exactly the test file payload structure
            payload = {
                "inputs": {
                    "keyword": keyword,
                    "language": language,
                    "transcription": combined_transcription.strip()  # Remove extra whitespace
                },
                "response_mode": "streaming",
                "user": "streamlit-app"
            }
            
            self.update_status(f"Preparing request to {self.kb_api_endpoint}")
            self.update_status(f"Keyword: {keyword}")
            self.update_status(f"Language: {language}")
            self.update_status(f"Transcription length: {len(combined_transcription)} characters")
            
            # Debug the request
            self.update_status("Request Headers:")
            for key, value in headers.items():
                if key.lower() != 'authorization':
                    self.update_status(f"{key}: {value}")
                else:
                    self.update_status(f"{key}: Bearer {api_key[:8]}...")
            
            self.update_status("Request Payload Preview:")
            preview_payload = {
                "inputs": {
                    "keyword": payload["inputs"]["keyword"],
                    "language": payload["inputs"]["language"],
                    "transcription_length": len(payload["inputs"]["transcription"])
                },
                "response_mode": payload["response_mode"],
                "user": payload["user"]
            }
            self.update_status(str(preview_payload))
            
            with st.spinner('Generating knowledge base... This might take a while.'):
                try:
                    self.update_status("Making API request...")
                    response = requests.post(
                        self.kb_api_endpoint,
                        headers=headers,
                        json=payload,
                        timeout=300
                    )
                    
                    self.update_status(f"Response status code: {response.status_code}")
                    self.update_status(f"Response headers: {dict(response.headers)}")
                    
                    # Log the complete response for debugging
                    self.update_status("Complete Response:")
                    self.update_status(response.text)
                    
                    # Try to parse response as JSON even if status code is not 200
                    try:
                        result = response.json() if response.text else None
                        self.update_status("Parsed response:")
                        self.update_status(str(result))
                        
                        # Check if response contains expected data structure
                        if isinstance(result, (list, dict)):
                            self.update_status("Knowledge base generated successfully!")
                            st.session_state['knowledge_base'] = result
                            return result
                        else:
                            self.update_status(f"Unexpected response format: {type(result)}", is_error=True)
                            return None
                            
                    except json.JSONDecodeError as e:
                        self.update_status(f"Failed to parse JSON response: {str(e)}", is_error=True)
                        self.update_status("Raw response received:")
                        self.update_status(response.text)
                        return None
                        
                except requests.exceptions.Timeout:
                    self.update_status("Request timed out after 5 minutes", is_error=True)
                    return None
                except requests.exceptions.RequestException as e:
                    self.update_status(f"Request failed: {str(e)}", is_error=True)
                    self.update_status(f"Request Exception Details: {repr(e)}")
                    return None
                    
        except Exception as e:
            self.update_status(f"Knowledge base generation error: {str(e)}", is_error=True)
            import traceback
            self.update_status(f"Full traceback:\n{traceback.format_exc()}", is_error=True)
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
    
    st.title("YouTube to MP3 Downloader & Transcriber")
    
    # Initialize the downloader
    downloader = YouTubeDownloader()
    
    # Create a placeholder for status messages
    downloader.status_placeholder = st.empty()
    
    # Get selected videos from session state
    selected_videos = st.session_state.get('selected_videos', [])
    
    # Get search keyword and language from session state
    keyword = st.session_state.get('last_query', '')
    language_code = st.session_state.get('last_language', 'en')
    
    if not selected_videos:
        # Show manual URL input if no videos were selected
        url = st.text_input("Enter YouTube URL:")
        title = "Manual Entry"
        if url:
            selected_videos = [{'url': url, 'title': title}]
            
        # If manual entry, also ask for keyword and language
        keyword = st.text_input("Enter keyword for knowledge base:", value=keyword)
        language_code = st.selectbox(
            "Select language:",
            ["en", "pl", "de", "fr", "es", "it", "ja", "ko", "ru"],
            index=["en", "pl", "de", "fr", "es", "it", "ja", "ko", "ru"].index(language_code)
        )
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
    
    # If we have any transcripts, combine them and process further
    if all_transcripts:
        st.success("All transcriptions complete!")
        
        # Store combined transcripts in session state if not already there
        if 'combined_transcription' not in st.session_state:
            combined_text = ""
            for t in all_transcripts:
                combined_text += f"\n\n{'='*50}\n"
                combined_text += f"Title: {t['title']}\n"
                combined_text += f"URL: {t['url']}\n"
                combined_text += f"{'='*50}\n\n"
                combined_text += t['transcript']
            st.session_state.combined_transcription = combined_text
        
        # Display combined transcript
        st.subheader("Combined Transcript:")
        st.text_area("", st.session_state.combined_transcription, height=300)
        
        # Download button for combined transcript
        st.download_button(
            label="Download Combined Transcript",
            data=st.session_state.combined_transcription,
            file_name="combined_transcripts.txt",
            mime="text/plain"
        )
        
        # Generate knowledge base
        if st.button("Generate Knowledge Base"):
            with st.spinner('Generating knowledge base...'):
                progress_bar = st.progress(0)
                
                progress_bar.progress(25)
                st.write("Preparing data...")
                
                progress_bar.progress(50)
                st.write("Sending data to API...")
                
                result = downloader.generate_knowledge_base(
                    keyword=keyword,
                    language_code=language_code,
                    combined_transcription=st.session_state.combined_transcription
                )
                
                if result is not None:  # Changed from if result:
                    progress_bar.progress(100)
                    st.success("Knowledge base generated successfully!")
                    st.write("API Response:")
                    st.json(result)
                else:
                    progress_bar.progress(0)
                    st.error("Failed to generate knowledge base. Check the status messages above for details.")
        
        # Clear selected videos and transcription after processing
        if 'selected_videos' in st.session_state:
            if st.button("Clear Selected Videos"):
                st.session_state.selected_videos = []
                if 'combined_transcription' in st.session_state:
                    del st.session_state.combined_transcription
                st.rerun()

if __name__ == "__main__":
    main() 