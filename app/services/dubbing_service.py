import os
from pydub import AudioSegment
from app.services.chatgpt_service import ChatGPTService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.youtube_service import YouTubeService

class DubbingService:
    def __init__(self):
        self.chatgpt = ChatGPTService()
        self.elevenlabs = ElevenLabsService()
        self.youtube = YouTubeService()
    
    def convert_timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp to seconds for synchronization"""
        parts = timestamp.replace(',', '.').split(':')
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        elif len(parts) == 2:  # MM:SS.mmm
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        return 0
    
    def create_synchronized_audio(self, video_url: str, target_language: str = "Urdu") -> str:
        """
        Create dubbed audio synchronized with video timestamps
        Returns path to final audio file
        """
        try:
            # Get transcript with timestamps
            transcript = self.youtube.get_transcript_with_timestamps(video_url)
            if not transcript:
                raise Exception("No transcript available for this video")
            
            # Create directory for audio segments
            os.makedirs("app/temp_uploads/audio_segments", exist_ok=True)
            segments_info = []
            
            # Process each segment
            for i, (start_time, end_time, english_text) in enumerate(transcript):
                # Translate text
                urdu_text = self.chatgpt.translate_text(english_text, target_language)
                
                # Generate audio
                audio_bytes = self.elevenlabs.text_to_speech(urdu_text)
                segment_file = f"app/temp_uploads/audio_segments/segment_{i:03d}.mp3"
                self.elevenlabs.save_audio_to_file(audio_bytes, segment_file)
                
                # Calculate timing
                start_seconds = self.convert_timestamp_to_seconds(start_time)
                end_seconds = self.convert_timestamp_to_seconds(end_time)
                original_duration = end_seconds - start_seconds
                
                segments_info.append({
                    'start_time': start_seconds,
                    'end_time': end_seconds,
                    'original_duration': original_duration,
                    'audio_file': segment_file,
                    'english_text': english_text,
                    'translated_text': urdu_text
                })
            
            # Create final synchronized audio
            final_audio = AudioSegment.silent(duration=0)
            current_position = 0
            
            for segment in segments_info:
                # Load generated audio
                segment_audio = AudioSegment.from_mp3(segment['audio_file'])
                segment_duration = len(segment_audio) / 1000.0
                
                # Calculate silence needed
                silence_needed = segment['start_time'] - current_position
                
                if silence_needed > 0:
                    silence = AudioSegment.silent(duration=int(silence_needed * 1000))
                    final_audio += silence
                    current_position += silence_needed
                
                # Add segment audio
                final_audio += segment_audio
                current_position += segment_duration
            
            # Export final audio
            final_output = "app/temp_uploads/final_dubbed_audio.mp3"
            final_audio.export(final_output, format="mp3")
            
            # Cleanup segment files
            for segment in segments_info:
                if os.path.exists(segment['audio_file']):
                    os.remove(segment['audio_file'])
            
            return final_output
            
        except Exception as e:
            # Cleanup on error
            if os.path.exists("app/temp_uploads/audio_segments"):
                for file in os.listdir("app/temp_uploads/audio_segments"):
                    os.remove(f"app/temp_uploads/audio_segments/{file}")
            raise e
        