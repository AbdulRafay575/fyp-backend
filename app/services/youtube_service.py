import yt_dlp
import requests
import re
from typing import List, Tuple, Optional
import math

class YouTubeService:
    def get_transcript_with_timestamps(self, video_url: str) -> Optional[List[Tuple[str, str, str]]]:
        """Extract English transcript from YouTube video with timestamps"""
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'vtt',
            'subtitleslangs': ['en'],
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Get video duration to handle long videos
                duration = info.get('duration', 0)
                if duration > 3600:  # Longer than 1 hour
                    print(f"Long video detected: {duration} seconds")
                
                subtitles = info.get("subtitles", {})
                auto_subs = info.get("automatic_captions", {})

                english_variants = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']

                # Try manual subtitles first
                for lang in english_variants:
                    if lang in subtitles and subtitles[lang]:
                        subtitle_url = subtitles[lang][-1]['url']
                        return self._download_and_parse_subtitle(subtitle_url)

                # Try auto-generated subtitles
                for lang in english_variants:
                    if lang in auto_subs and auto_subs[lang]:
                        subtitle_url = auto_subs[lang][-1]['url']
                        return self._download_and_parse_subtitle(subtitle_url)

                # Try any English variant
                for lang in list(subtitles.keys()) + list(auto_subs.keys()):
                    if lang.startswith('en') or '-en' in lang:
                        source = subtitles if lang in subtitles else auto_subs
                        subtitle_url = source[lang][-1]['url']
                        return self._download_and_parse_subtitle(subtitle_url)

                return None

        except Exception as e:
            raise Exception(f"YouTube transcript error: {str(e)}")

    def _download_and_parse_subtitle(self, url: str) -> List[Tuple[str, str, str]]:
        """Download and parse subtitle content with timestamps"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            vtt_data = response.text

            lines = vtt_data.splitlines()
            subtitles = []
            current_block = []
            start_time = None
            end_time = None

            for line in lines:
                line = line.strip()

                if line.startswith(('WEBVTT', 'NOTE', 'X-TIMESTAMP-MAP', 'Kind:')):
                    continue

                timestamp_match = re.match(r'(\d+:\d+:\d+\.\d+)\s*-->\s*(\d+:\d+:\d+\.\d+)', line)
                if timestamp_match:
                    if current_block and start_time and end_time:
                        text = ' '.join(current_block)
                        if text.strip():  # Only add non-empty blocks
                            subtitles.append((start_time, end_time, text))
                        current_block = []

                    start_time = timestamp_match.group(1)
                    end_time = timestamp_match.group(2)
                    continue

                simple_timestamp_match = re.match(r'(\d+:\d+\.\d+)\s*-->\s*(\d+:\d+\.\d+)', line)
                if simple_timestamp_match:
                    if current_block and start_time and end_time:
                        text = ' '.join(current_block)
                        if text.strip():
                            subtitles.append((start_time, end_time, text))
                        current_block = []

                    start_time = simple_timestamp_match.group(1)
                    end_time = simple_timestamp_match.group(2)
                    continue

                if line and not re.match(r'^\d+$', line) and '-->' not in line:
                    # Clean the text
                    cleaned_line = re.sub(r'^\d+\s*', '', line)
                    cleaned_line = re.sub(r'^[^a-zA-Z0-9]+', '', cleaned_line)
                    if cleaned_line.strip():
                        current_block.append(cleaned_line.strip())

            if current_block and start_time and end_time:
                text = ' '.join(current_block)
                if text.strip():
                    subtitles.append((start_time, end_time, text))

            return subtitles

        except Exception as e:
            raise Exception(f"Subtitle parsing error: {str(e)}")

    def get_transcript_text_only(self, transcript_with_timestamps: List[Tuple[str, str, str]]) -> str:
        """Convert timestamped transcript to clean text only"""
        if not transcript_with_timestamps:
            return ""
        
        text_parts = []
        for _, _, text in transcript_with_timestamps:
            cleaned_text = re.sub(r'\d+', '', text)
            cleaned_text = re.sub(r'[^\w\s.,!?]', '', cleaned_text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            if cleaned_text:
                text_parts.append(cleaned_text)
        
        full_text = " ".join(text_parts)
        
        # For very long transcripts, truncate but keep important parts
        if len(full_text) > 50000:
            # Keep first 40k and last 10k characters
            full_text = full_text[:40000] + " [...] " + full_text[-10000:]
        
        return full_text

    def chunk_transcript_by_time(self, transcript_with_timestamps: List[Tuple[str, str, str]], chunk_minutes: int = 5) -> List[str]:
        """Split transcript into time-based chunks - improved for long videos"""
        if not transcript_with_timestamps:
            return []
        
        chunks = []
        current_chunk = []
        current_start_time = None
        chunk_duration = chunk_minutes * 60
        
        for start_time, end_time, text in transcript_with_timestamps:
            start_seconds = self._timestamp_to_seconds(start_time)
            end_seconds = self._timestamp_to_seconds(end_time)
            
            if current_start_time is None:
                current_start_time = start_seconds
            
            # If this segment would push us over the chunk duration, start new chunk
            if start_seconds - current_start_time > chunk_duration and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [text]
                current_start_time = start_seconds
            else:
                current_chunk.append(text)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def chunk_transcript_by_size(self, text: str, max_chars: int = 8000) -> List[str]:
        """Split text into size-based chunks for API limits"""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size > max_chars:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_size = word_size
                else:
                    # Single word longer than max_chars, split it
                    chunks.append(word[:max_chars])
                    current_chunk = [word[max_chars:]] if len(word) > max_chars else []
                    current_size = len(word[max_chars:]) if len(word) > max_chars else 0
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp string to seconds"""
        parts = timestamp.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        elif len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        return 0.0