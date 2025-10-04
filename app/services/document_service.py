try:
    import pypdf
except ImportError:
    import PyPDF2 as pypdf
import docx
import os

class DocumentService:
    def extract_text(self, file_path: str) -> str:
        """Extract text from various document formats"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif ext in ['.doc', '.docx']:
                return self._extract_from_docx(file_path)
            elif ext == '.txt':
                return self._extract_from_txt(file_path)
            elif ext in ['.ppt', '.pptx']:
                return self._extract_from_ppt(file_path)
            else:
                return self._extract_from_txt(file_path)
                
        except Exception as e:
            raise Exception(f"Text extraction error: {str(e)}")
    
    def extract_text_chunked(self, file_path: str, chunk_size: int = 2000) -> list:
        """Extract text and split into chunks for long documents"""
        try:
            full_text = self.extract_text(file_path)
            return self._split_into_chunks(full_text, chunk_size)
        except Exception as e:
            raise Exception(f"Chunked text extraction error: {str(e)}")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pypdf"""
        try:
            with open(file_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"PDF extraction error: {str(e)}")
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"DOCX extraction error: {str(e)}")
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read().strip()
        except Exception as e:
            raise Exception(f"TXT extraction error: {str(e)}")
    
    def _extract_from_ppt(self, file_path: str) -> str:
        """Extract text from PPT (basic implementation)"""
        try:
            # Placeholder for PPT extraction
            # You can implement proper PPT extraction with python-pptx later
            return "PPT text extraction would be implemented here. Currently using basic text extraction."
        except Exception as e:
            raise Exception(f"PPT extraction error: {str(e)}")
    
    def _split_into_chunks(self, text: str, chunk_size: int = 2000) -> list:
        """Split text into chunks of approximately chunk_size characters"""
        if not text:
            return []
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first for better context
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # If paragraph is very long, split by sentences
            if len(paragraph) > chunk_size:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if sentence[-1] != '.':
                        sentence += '.'
                    
                    if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
            else:
                if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                    current_chunk += paragraph + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        print(f"Split text into {len(chunks)} chunks")
        return chunks