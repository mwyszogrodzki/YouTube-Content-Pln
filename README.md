# YouTube Search and Download

A Python application for searching YouTube videos and downloading/transcribing audio.

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your API keys:
   ```
   RAPIDAPI_KEY=your_rapidapi_key
   GROQ_API_KEY=your_groq_api_key
   ```
4. Run the applications:
   ```bash
   streamlit run youtube_search.py
   # or
   python youtube_downloader.py
   ```

## Required API Keys

You'll need:
- RapidAPI key (for YouTube search and MP3 conversion)
- Groq API key (for audio transcription)

Get your API keys from:
- RapidAPI: https://rapidapi.com/
- Groq: https://console.groq.com/

## Environment Variables

Create a `.env` file with: 