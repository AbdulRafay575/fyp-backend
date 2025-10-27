import requests
import json
import time
from app.config import settings
import aiohttp
import json

class ChatGPTService:
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.endpoint = "https://models.github.ai/inference"
        self.model = "openai/gpt-4.1-mini"
    
    def get_summary(self, text: str):
        """Get summary for text"""
        system_prompt = f"""
       You are summarizing a segment of a YouTube video.

🎯 Objective:
Create a clear and well-structured summary of this specific segment.

📋 Guidelines:
- Capture **all key ideas, insights, facts, and topics** discussed in this segment.
- **Remove filler words**, repetition, and casual speech patterns.
- **Do not mention speakers** (e.g., “the host said”, “she explains”).
- **Ignore any promotional or sponsored content** that does not add to the video’s core message.
- Write from a **neutral, third-person perspective**.
- Maintain a **professional, educational, and informative tone**.
- Use **short paragraphs or bullet points** for readability.
- Focus on delivering **complete and coherent information** from this segment — it should make sense even without other parts.
- Avoid assumptions or adding information not present in the text.

📘 Output Format:
A single well-written paragraph (or short set of paragraphs) summarizing this segment clearly and professionally.
        """
        
        return self._make_request(system_prompt, text)
    
    def get_chunked_summary(self, text_chunks: list):
        """Get summary for chunked text - improved for long documents"""
        if not text_chunks:
            return "No content to summarize"
        
        print(f"Processing {len(text_chunks)} chunks...")
        
        # For very long documents, process in batches
        if len(text_chunks) > 10:
            return self._process_large_document(text_chunks)
        
        chunk_summaries = []
        
        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i+1}/{len(text_chunks)}...")
            
            system_prompt = f"""
           You are creating a final, comprehensive summary by combining summaries of multiple video segments.

🧠 Objective:
Produce a cohesive and well-structured final summary that reads naturally, as if summarizing the entire video in one flow.

📋 Guidelines:
- Capture **all key ideas, insights, facts, and topics** discussed throughout the video.
- **Eliminate filler words**, repetition, and personal speech patterns.
- **Do not mention speakers** (e.g., “the host said”, “she explains”).
- **Exclude promotional or sponsored content** — focus only on educational, informational, or main thematic material.
- Write from a **neutral, third-person perspective**.
- Maintain a **professional and informative tone**.
- Use **short paragraphs or clear bullet points** for readability.
- Ensure the summary feels **complete and cohesive**, not like separated parts.
- Do **not** add new information or assumptions not present in the provided summaries.

📘 Output Format:
A well-written paragraph (or short set of paragraphs) that reads like a complete, natural summary of the entire video that is concise.
           """
            
            try:
                chunk_summary = self._make_request(system_prompt, chunk[:5000])  # Limit chunk size
                chunk_summaries.append(chunk_summary)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                chunk_summaries.append(f"Segment {i+1}: [Summary unavailable]")
        
        return self._combine_chunk_summaries(chunk_summaries)
    




    def generate_questions(self, text: str, num_questions: int = 5):
        """Generate practice questions from text"""
        system_prompt = f"""
        You are an educational question generator. Create {num_questions} practice questions based on the provided text.
        
        Format your response as:
        QUESTIONS:
        1. [Question 1]
        2. [Question 2]
        3. [Question 3]
        4. [Question 4]
        5. [Question 5]
        
        ANSWERS:
        1. [Answer 1]
        2. [Answer 2]
        3. [Answer 3]
        4. [Answer 4]
        5. [Answer 5]
        
        Make questions diverse: multiple choice, short answer, and conceptual questions.
        """
        
        return self._make_request(system_prompt, text)
    
    def generate_chunked_questions(self, text_chunks: list, num_questions: int = 10):
        """Generate questions from chunked text for long documents"""
        if not text_chunks:
            return "No content to generate questions from"
        
        print(f"Generating questions from {len(text_chunks)} chunks...")
        
        # For very long documents, sample key segments
        if len(text_chunks) > 8:
            text_chunks = self._sample_document_chunks(text_chunks)
        
        all_questions = []
        
        for i, chunk in enumerate(text_chunks):
            print(f"Generating questions from chunk {i+1}/{len(text_chunks)}...")
            
            system_prompt = f"""
            You are generating practice questions from part {i+1} of {len(text_chunks)} of a document.
            Create 2-3 high-quality questions from this segment.
            Include answers for each question.
            """
            
            try:
                chunk_questions = self._make_request(system_prompt, chunk[:4000])
                all_questions.append(chunk_questions)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error generating questions from chunk {i+1}: {e}")
                all_questions.append(f"Questions from segment {i+1}: [Unavailable]")
        
        return self._combine_questions(all_questions, num_questions)
    
    def _process_large_document(self, text_chunks: list):
        """Process very long documents by sampling key segments"""
        print("Large document detected, using sampling strategy...")
        
        sampled_chunks = self._sample_document_chunks(text_chunks)
        print(f"Sampled {len(sampled_chunks)} key segments from {len(text_chunks)} total chunks")
        
        return self.get_chunked_summary(sampled_chunks)
    
    def _sample_document_chunks(self, text_chunks: list) -> list:
        """Sample representative chunks from document"""
        total_chunks = len(text_chunks)
        sample_indices = []
        
        # Always include first and last chunks
        sample_indices.append(0)
        if total_chunks > 1:
            sample_indices.append(total_chunks - 1)
        
        # Include middle chunks 
        if total_chunks > 3:
            middle = total_chunks // 2
            sample_indices.append(middle)
            if total_chunks > 5:
                sample_indices.append(middle - 1)
                sample_indices.append(middle + 1)
        
        # Include some random chunks for diversity
        if total_chunks > 8:
            import random
            extra_samples = min(3, total_chunks - len(sample_indices))
            available_indices = [i for i in range(total_chunks) if i not in sample_indices]
            sample_indices.extend(random.sample(available_indices, extra_samples))
        
        return [text_chunks[i] for i in sorted(set(sample_indices))]
    
    def _combine_chunk_summaries(self, chunk_summaries: list):
        """Combine individual chunk summaries into final summary"""
        combined_text = "\n\n".join([
            f"PART {i+1} SUMMARY:\n{summary}" 
            for i, summary in enumerate(chunk_summaries)
        ])
        
        system_prompt = f"""
       You are creating a final, comprehensive summary by combining summaries of multiple video segments.

🧠 Objective:
Produce a cohesive and well-structured final summary that reads naturally, as if summarizing the entire video in one flow.

📋 Guidelines:
- Capture **all key ideas, insights, facts, and topics** discussed throughout the video.
- **Eliminate filler words**, repetition, and personal speech patterns.
- **Do not mention speakers** (e.g., “the host said”, “she explains”).
- **Exclude promotional or sponsored content** — focus only on educational, informational, or main thematic material.
- Write from a **neutral, third-person perspective**.
- Maintain a **professional and informative tone**.
- Use **short paragraphs or clear bullet points** for readability.
- Ensure the summary feels **complete and cohesive**, not like separated parts.
- Do **not** add new information or assumptions not present in the provided summaries.

📘 Output Format:
A well-written paragraph (or short set of paragraphs) that reads like a complete, natural summary of the entire video.
        
        """
        
        return self._make_request(system_prompt, combined_text)
    
    # Add this method to your existing ChatGPTService class
    def analyze_past_papers(self, study_material: str, past_paper: str, num_questions: int = 10):
        """Analyze past papers and generate questions based on patterns"""
        system_prompt = f"""
        You are an expert exam question predictor. Analyze the study material and past paper patterns to generate {num_questions} likely exam questions.
        
        STUDY MATERIAL: The content students need to learn
        PAST PAPER: Previous exam papers showing question patterns, formats, and difficulty levels
        
        Your task:
        1. Analyze the past paper to understand:
        - Question formats (multiple choice, short answer, essay, etc.)
        - Difficulty levels
        - Topic distribution
        - Marking schemes
        - Common themes and patterns
        
        2. Based on the study material content, generate {num_questions} questions that:
        - Match the past paper patterns and formats
        - Cover the most important topics from study material
        - Have appropriate difficulty levels
        - Include clear, concise answers
        
        Format your response as:
        
        ANALYSIS:
        [Brief analysis of past paper patterns and how they apply to study material]
        
        QUESTIONS:
        1. [Question 1 that matches past paper format]
        2. [Question 2 that matches past paper format]
        ...
        
        ANSWERS:
        1. [Detailed answer 1]
        2. [Detailed answer 2]
        ...
        
        Make the questions realistic and similar to what would appear in an actual exam.
        """
        
        content = f"""STUDY MATERIAL CONTENT:
    {study_material[:8000]}

    PAST PAPER CONTENT:
    {past_paper[:6000]}
    """
        
        return self._make_request(system_prompt, content)
    
    def _combine_questions(self, all_questions: list, num_questions: int):
        """Combine questions from chunks and select best ones"""
        combined_text = "\n\n".join([
            f"QUESTIONS FROM PART {i+1}:\n{questions}" 
            for i, questions in enumerate(all_questions)
        ])
        
        system_prompt = f"""
        You have questions from different parts of a document. Select and refine the {num_questions} best questions.
        
        Format your response as:
        
        QUESTIONS:
        1. [Best question 1]
        2. [Best question 2]
        3. [Best question 3]
        4. [Best question 4]
        5. [Best question 5]
        
        ANSWERS:
        1. [Clear answer 1]
        2. [Clear answer 2]
        3. [Clear answer 3]
        4. [Clear answer 4]
        5. [Clear answer 5]
        
        Ensure questions are diverse and cover different aspects of the document.
        Remove duplicates and select the most important questions.
        """
        
        return self._make_request(system_prompt, combined_text)
    
    def _make_request(self, system_prompt: str, user_content: str):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                f"{self.endpoint}/chat/completions", 
                headers=headers, 
                data=json.dumps(data),
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            raise Exception("ChatGPT API request timed out")
        except Exception as e:
            raise Exception(f"ChatGPT API error: {str(e)}")
    async def translate_text_async(self, text: str, target_language: str = "Urdu"):
        """Translate text to target language asynchronously"""
        system_prompt = f"""
        You are a translator from English to {target_language}.
        Translate all normal text to {target_language}.
        Keep technical terms, names, and proper nouns in English.
        Make the translation natural and easy to understand.
        Don't make it too formal - use common spoken language.
        """
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.endpoint}/chat/completions", 
                headers=headers, 
                data=json.dumps(data),
                timeout=30
            ) as response:
                result = await response.json()
                return result['choices'][0]['message']['content']