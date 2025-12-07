import re
import tiktoken
from typing import List, Dict
from config import Config

class TextProcessor:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\[\]{}"]', '', text)
        
        # Remove multiple consecutive punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        # Clean up spaces around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
        
        return text.strip()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be improved with spaCy or NLTK
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_chunks(self, text: str, metadata: Dict) -> List[Dict]:
        """Create text chunks with overlap and metadata"""
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_tokens = self.count_tokens(sentence)
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk with metadata
                chunk_data = {
                    'text': current_chunk.strip(),
                    'tokens': current_tokens,
                    'source_title': metadata['title'],
                    'source_url': metadata['url'],
                    'chunk_id': len(chunks)
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self.get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                current_tokens = self.count_tokens(current_chunk)
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens
            
            i += 1
        
        # Add final chunk if there's content
        if current_chunk.strip():
            chunk_data = {
                'text': current_chunk.strip(),
                'tokens': current_tokens,
                'source_title': metadata['title'],
                'source_url': metadata['url'],
                'chunk_id': len(chunks)
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get the last portion of text for overlap"""
        if overlap_tokens <= 0:
            return ""
        
        words = text.split()
        overlap_words = []
        current_tokens = 0
        
        # Work backwards from the end
        for word in reversed(words):
            word_tokens = self.count_tokens(word)
            if current_tokens + word_tokens > overlap_tokens:
                break
            overlap_words.insert(0, word)
            current_tokens += word_tokens
        
        return " ".join(overlap_words)
    
    def process_scraped_data(self, scraped_data: List[Dict]) -> List[Dict]:
        """Process all scraped data into chunks"""
        all_chunks = []
        
        for page_data in scraped_data:
            # Clean the text
            cleaned_text = self.clean_text(page_data['plain_text'])
            
            # Skip very short pages
            if len(cleaned_text) < 100:
                continue
            
            # Create metadata
            metadata = {
                'title': page_data['title'],
                'url': page_data['url']
            }
            
            # Create chunks
            chunks = self.create_chunks(cleaned_text, metadata)
            all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} chunks from {len(scraped_data)} pages")
        return all_chunks
    
    def filter_chunks_by_quality(self, chunks: List[Dict], min_tokens: int = 50) -> List[Dict]:
        """Filter out low-quality chunks"""
        quality_chunks = []
        
        for chunk in chunks:
            # Skip very short chunks
            if chunk['tokens'] < min_tokens:
                continue
            
            # Skip chunks that are mostly punctuation or numbers
            text = chunk['text']
            alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
            if alpha_ratio < 0.6:
                continue
            
            # Skip chunks with too many repeated words
            words = text.lower().split()
            if len(set(words)) / len(words) < 0.5 if words else True:
                continue
            
            quality_chunks.append(chunk)
        
        print(f"Filtered {len(chunks)} chunks down to {len(quality_chunks)} quality chunks")
        return quality_chunks

if __name__ == "__main__":
    # Test the text processor
    processor = TextProcessor()
    
    sample_text = """
    This is a sample text for testing the chunking functionality. 
    It should be split into appropriate chunks based on the token limit.
    Each chunk should maintain some overlap with the previous chunk.
    This helps ensure context is preserved across chunk boundaries.
    """
    
    metadata = {
        'title': 'Test Page',
        'url': 'https://example.com/test'
    }
    
    chunks = processor.create_chunks(sample_text, metadata)
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {chunk['tokens']} tokens")
        print(f"Text: {chunk['text'][:100]}...")
        print()