import tkinter as tk
from tkinter import ttk
import re
import json
import time
import requests
import threading
import webbrowser
from itertools import cycle
import os
import subprocess
from groq import Groq
from tkinter import filedialog

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube to MP3 Downloader")
        self.root.geometry("400x200")
        
        # URL Entry
        self.url_frame = ttk.Frame(root, padding="10")
        self.url_frame.pack(fill=tk.X)
        
        self.url_label = ttk.Label(self.url_frame, text="YouTube URL:")
        self.url_label.pack()
        
        self.url_entry = ttk.Entry(self.url_frame, width=50)
        self.url_entry.pack(pady=5)
        
        # Download Button
        self.download_btn = ttk.Button(root, text="Convert to MP3", command=self.start_conversion)
        self.download_btn.pack(pady=10)
        
        # Status Label
        self.status_label = ttk.Label(root, text="")
        self.status_label.pack(pady=10)
        
        # Loading animation characters
        self.loading_chars = cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.is_loading = False
        
        # Add transcript text area
        self.transcript_frame = ttk.Frame(root, padding="10")
        self.transcript_frame.pack(fill=tk.BOTH, expand=True)
        
        self.transcript_text = tk.Text(self.transcript_frame, height=10, width=50)
        self.transcript_text.pack(fill=tk.BOTH, expand=True)
        
        # Add save transcript button (hidden by default)
        self.save_transcript_btn = ttk.Button(
            root,
            text="Save Transcript",
            command=self.save_transcript,
            state='disabled'
        )
        self.save_transcript_btn.pack(pady=5)
        
        # Store transcript
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

    def update_loading_animation(self):
        """Update loading animation"""
        if self.is_loading:
            self.status_label['text'] = f"Converting {next(self.loading_chars)}"
            self.root.after(100, self.update_loading_animation)

    def check_conversion_status(self, video_id):
        """Check conversion status from API"""
        headers = {
            'x-rapidapi-key': "8045e3125cmsh2a1994c6d67e2cap18598bjsnbf7aafc18393",
            'x-rapidapi-host': "youtube-mp36.p.rapidapi.com"
        }
        
        while self.is_loading:
            try:
                response = requests.get(
                    f"https://youtube-mp36.p.rapidapi.com/dl?id={video_id}",
                    headers=headers
                )
                data = response.json()
                
                if data.get('status') == 'ok':
                    self.is_loading = False
                    self.root.after(0, self.show_download_link, data.get('link'))
                    break
                    
                time.sleep(2)
                
            except Exception as e:
                self.is_loading = False
                self.root.after(0, self.show_error, str(e))
                break

    def download_and_process_file(self, url):
        """Download MP3 and process it"""
        try:
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
            client = Groq(
                api_key="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"
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
            
            # Update UI with transcript
            self.current_transcript = transcription.text
            self.root.after(0, self.show_transcript)
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Processing error: {str(e)}")

    def show_transcript(self):
        """Display transcript in the UI"""
        self.transcript_text.delete('1.0', tk.END)
        self.transcript_text.insert('1.0', self.current_transcript)
        self.save_transcript_btn['state'] = 'normal'
        self.status_label['text'] = "Transcription complete!"

    def save_transcript(self):
        """Save transcript to a text file"""
        if not self.current_transcript:
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save Transcript"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.current_transcript)

    def show_download_link(self, link):
        """Show download link and update UI"""
        self.status_label['text'] = "Starting download and processing..."
        
        # Start processing in a separate thread
        threading.Thread(
            target=self.download_and_process_file,
            args=(link,),
            daemon=True
        ).start()

    def show_error(self, error_message):
        """Show error message"""
        self.status_label['text'] = f"Error: {error_message}"
        self.download_btn['state'] = 'normal'

    def start_conversion(self):
        """Start the conversion process"""
        url = self.url_entry.get().strip()
        video_id = self.extract_video_id(url)
        
        if not video_id:
            self.status_label['text'] = "Invalid YouTube URL"
            return
        
        self.download_btn['state'] = 'disabled'
        self.is_loading = True
        self.update_loading_animation()
        
        # Start checking status in a separate thread
        threading.Thread(
            target=self.check_conversion_status,
            args=(video_id,),
            daemon=True
        ).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop() 