"""
File Extraction Service
Extracts text content from various file formats
"""
import os
from typing import List, Dict, Any
import fitz  # PyMuPDF
from docx import Document
import pytesseract
from PIL import Image


class TextExtractor:
    """Extract text from various file formats"""
    
    @staticmethod
    def extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF files using PyMuPDF"""
        text_parts = []
        
        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")
            doc.close()
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def extract_from_docx(file_path: str) -> str:
        """Extract text from DOCX files"""
        text_parts = []
        
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        text_parts.append(row_text)
        except Exception as e:
            raise Exception(f"Error extracting DOCX: {str(e)}")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def extract_from_markdown(file_path: str) -> str:
        """Extract text from Markdown files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading Markdown: {str(e)}")
    
    @staticmethod
    def extract_from_text(file_path: str) -> str:
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}")
    
    @staticmethod
    def extract_from_image(file_path: str) -> str:
        """Extract text from images using OCR (Tesseract)"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting from image: {str(e)}")
    
    @classmethod
    def extract(cls, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a file based on its extension.
        Returns dict with content and metadata.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        extractors = {
            '.pdf': cls.extract_from_pdf,
            '.docx': cls.extract_from_docx,
            '.md': cls.extract_from_markdown,
            '.txt': cls.extract_from_text,
            '.png': cls.extract_from_image,
            '.jpg': cls.extract_from_image,
            '.jpeg': cls.extract_from_image,
        }
        
        extractor = extractors.get(ext)
        if not extractor:
            raise ValueError(f"Unsupported file type: {ext}")
        
        content = extractor(file_path)
        
        return {
            "filename": filename,
            "file_path": file_path,
            "file_type": ext,
            "content": content,
            "char_count": len(content),
            "word_count": len(content.split())
        }
    
    @classmethod
    def extract_multiple(cls, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Extract text from multiple files"""
        results = []
        for file_path in file_paths:
            try:
                result = cls.extract(file_path)
                results.append(result)
            except Exception as e:
                results.append({
                    "filename": os.path.basename(file_path),
                    "file_path": file_path,
                    "error": str(e)
                })
        return results


class TextChunker:
    """Split text into meaningful chunks for embedding"""
    
    def __init__(
        self, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        Returns list of chunks with metadata.
        """
        if not text or len(text) < self.min_chunk_size:
            return [{
                "content": text,
                "index": 0,
                "start_char": 0,
                "end_char": len(text),
                **(metadata or {})
            }] if text else []
        
        chunks = []
        start = 0
        index = 0
        
        while start < len(text):
            # Find end of chunk
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for sep in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + self.min_chunk_size:
                        end = last_sep + len(sep)
                        break
            
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    "content": chunk_text,
                    "index": index,
                    "start_char": start,
                    "end_char": end,
                    **(metadata or {})
                })
                index += 1
            
            # Move start with overlap
            start = end - self.chunk_overlap
            if start >= len(text) - self.min_chunk_size:
                break
        
        return chunks
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk multiple documents"""
        all_chunks = []
        
        for doc in documents:
            if "error" in doc:
                continue
            
            metadata = {
                "filename": doc.get("filename"),
                "file_type": doc.get("file_type")
            }
            
            chunks = self.chunk_text(doc.get("content", ""), metadata)
            all_chunks.extend(chunks)
        
        return all_chunks


# Convenience instances
extractor = TextExtractor()
chunker = TextChunker()
