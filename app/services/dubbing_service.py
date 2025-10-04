import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
import aiohttp
import json
from app.services.chatgpt_service import ChatGPTService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.youtube_service import YouTubeService
from app.config import settings

class DubbingService:
    def __init__(self):
        self.chatgpt = ChatGPTService()
        self.elevenlabs = ElevenLabsService()
        self.youtube = YouTubeService()
        self.executor = ThreadPoolExecutor(max_workers=3)  # Reduced for stability
    
    def convert_timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp to seconds for synchronization"""
        try:
            # Handle different timestamp formats
            if ',' in timestamp:
                timestamp = timestamp.replace(',', '.')
            
            parts = timestamp.split(':')
            if len(parts) == 3:  # HH:MM:SS.mmm
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            elif len(parts) == 2:  # MM:SS.mmm
                minutes, seconds = parts
                return int(minutes) * 60 + float(seconds)
            else:  # Just seconds
                return float(timestamp)
        except Exception:
            return 0
    
    async def process_segment(self, segment_data):
        """Process a single segment in parallel"""
        i, start_time, end_time, english_text = segment_data
        
        try:
            print(f"Processing segment {i}: {english_text[:50]}...")
            
            # Skip very short segments
            if len(english_text.strip()) < 10:
                return {
                    'success': False,
                    'error': 'Text too short',
                    'segment_index': i
                }
            
            # Translate text
            urdu_text = await self.chatgpt.translate_text_async(english_text, "Urdu")
            
            # Generate audio
            audio_bytes = await self.elevenlabs.text_to_speech_async(urdu_text)
            
            # Create segments directory if it doesn't exist
            os.makedirs("app/temp_uploads/audio_segments", exist_ok=True)
            
            segment_file = f"app/temp_uploads/audio_segments/segment_{i:03d}.mp3"
            self.elevenlabs.save_audio_to_file(audio_bytes, segment_file)
            
            # Calculate timing
            start_seconds = self.convert_timestamp_to_seconds(start_time)
            end_seconds = self.convert_timestamp_to_seconds(end_time)
            original_duration = end_seconds - start_seconds
            
            return {
                'start_time': start_seconds,
                'end_time': end_seconds,
                'original_duration': original_duration,
                'audio_file': segment_file,
                'english_text': english_text,
                'translated_text': urdu_text,
                'success': True
            }
        except Exception as e:
            print(f"Error processing segment {i}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'segment_index': i
            }
    
    async def create_synchronized_audio(self, video_url: str, target_language: str = "Urdu") -> str:
        """
        Create dubbed audio synchronized with video timestamps using parallel processing
        """
        try:
            # Get transcript with timestamps
            print("Getting transcript...")
            transcript = self.youtube.get_transcript_with_timestamps(video_url)
            if not transcript:
                raise Exception("No transcript available for this video")
            
            print(f"Processing {len(transcript)} segments...")
            
            # Create directory for audio segments
            os.makedirs("app/temp_uploads/audio_segments", exist_ok=True)
            
            # Prepare segment data for parallel processing
            segment_data_list = [
                (i, start_time, end_time, english_text) 
                for i, (start_time, end_time, english_text) in enumerate(transcript)
            ]
            
            # Limit number of segments for testing
            if len(segment_data_list) > 20:
                print(f"Limiting to first 20 segments out of {len(segment_data_list)}")
                segment_data_list = segment_data_list[:20]
            
            # Process segments in parallel with limited concurrency
            semaphore = asyncio.Semaphore(2)  # Limit concurrent requests
            
            async def process_with_semaphore(segment_data):
                async with semaphore:
                    return await self.process_segment(segment_data)
            
            tasks = [process_with_semaphore(segment_data) for segment_data in segment_data_list]
            segments_info = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful segments
            successful_segments = [seg for seg in segments_info if isinstance(seg, dict) and seg.get('success')]
            failed_segments = [seg for seg in segments_info if isinstance(seg, dict) and not seg.get('success')]
            
            if failed_segments:
                print(f"Failed to process {len(failed_segments)} segments")
            
            if not successful_segments:
                raise Exception("No segments were processed successfully")
            
            print(f"Successfully processed {len(successful_segments)} segments")
            
            # Sort segments by start time
            successful_segments.sort(key=lambda x: x['start_time'])
            
            # Create final synchronized audio
            final_audio = AudioSegment.silent(duration=0)
            current_position = 0
            
            for segment in successful_segments:
                try:
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
                    
                except Exception as e:
                    print(f"Error adding segment to final audio: {str(e)}")
                    continue
            
            # Export final audio
            final_output = f"app/temp_uploads/final_dubbed_audio_{os.urandom(4).hex()}.mp3"
            final_audio.export(final_output, format="mp3", bitrate="128k")
            
            print(f"Final audio created: {final_output}")
            
            # Cleanup segment files
            for segment in successful_segments:
                if os.path.exists(segment['audio_file']):
                    try:
                        os.remove(segment['audio_file'])
                    except:
                        pass
            
            return final_output
            
        except Exception as e:
            # Cleanup on error
            print(f"Dubbing error: {str(e)}")
            if os.path.exists("app/temp_uploads/audio_segments"):
                for file in os.listdir("app/temp_uploads/audio_segments"):
                    try:
                        os.remove(f"app/temp_uploads/audio_segments/{file}")
                    except:
                        pass
            raise e