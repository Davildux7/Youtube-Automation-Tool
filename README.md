# Youtube Automation Tool

A modular Python application with a modern GUI (CustomTkinter) designed to automate video processing tasks and YouTube market research.

## Features

1.  **Watermark Overlay**: Automatically applies a transparent image overlay (watermark) to video files.
2.  **AI Subtitles**: Extracts audio from video and generates `.srt` subtitle files using the **Groq API** (Whisper model).
3.  **YouTube Prospector**: Scrapes YouTube for videos based on specific niches, view counts, duration, and upload date filters to find viral leads.

## Prerequisites

*   **Python 3.8+**
*   **FFmpeg**: Required for audio extraction (must be installed and added to your system's PATH).
*   **Groq API Key**: Required for subtitle generation.
*   **Every module that's on `requirements.txt`

## Configuration

1.  **Environment Variables**:
    Create a `.env` file in the root following the `.env.example` template

2.  **Watermark Image**:
    Place a PNG image named `watermark.png` in the root folder. This image will be used for the watermarking feature. (can have transparent background)

## Usage

Run the main application script:

```bash
python main.py
```

### How to use the tabs:

*   **Watermark:** Select a video file. The tool will overlay `watermark.png` and save the result.
*   **Whisper Subtitles:** Enter your API Key (if not in `.env`), select a video, and click "Generate Subtitles". An `.srt` file will be created in the same folder.
*   **YouTube Hunter:** Enter search terms (one per line), set your filters (Views, Days Ago), and click "Start Hunt". Results are saved to `youtube_leads.csv`.

## Project Structure

```text
.
├── main.py                 # Application entry point
├── config.py               # Global settings and fixes
├── services/               # Logic modules
│   ├── youtube.py          # YouTube scraping logic
│   ├── video.py            # Watermarking logic
│   └── audio.py            # Audio extraction & Transcription
├── ui/                     # User Interface
│   └── interface.py        # GUI implementation
├── watermark.png           # Your watermark image
└── .env                    # API Keys
```

## License

This project is open-source. Feel free to modify it.
