import os
import math
import subprocess
from groq import Groq

class SRTConverter:
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        if seconds < 0: seconds = 0
        frac, whole = math.modf(seconds)
        return f"{int(whole // 3600):02d}:{int((whole % 3600) // 60):02d}:{int(whole % 60):02d},{int(frac * 1000):03d}"

    @staticmethod
    def save_srt(segments, output_path: str):
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for i, entry in enumerate(segments):
                    start = entry.get('start', 0)
                    end = entry.get('end', 0)
                    text = entry.get('text', '').strip()
                    f.write(f"{i + 1}\n")
                    f.write(f"{SRTConverter.format_timestamp(start)} --> {SRTConverter.format_timestamp(end)}\n")
                    f.write(f"{text}\n\n")
        except IOError as e:
            raise Exception(f"Error saving SRT file: {e}")

class AudioProcessor:
    @staticmethod
    def extract_audio(video_path: str, audio_output_path: str):
        # !!!!! FFMPEG MUST BE IN PATH !!!!!!!!!
        command = ['ffmpeg', '-y', '-i', video_path, '-vn', '-ac', '1', '-ar', '16000', '-ab', '32k', '-f', 'mp3', audio_output_path]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            subprocess.run(command, check=True, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Error extracting audio. Check if FFmpeg is installed and in PATH.")

class GroqService:
    @staticmethod
    def transcribe(api_key: str, audio_path: str):
        if not api_key: raise ValueError("Groq API Key was not provided.")
        client = Groq(api_key=api_key)
        if not os.path.exists(audio_path): raise FileNotFoundError("Audio file not found.")
        
        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
                language="en" 
            )
        return transcription