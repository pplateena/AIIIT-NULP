import chromadb
import json
import os
from typing import List, Dict, Optional, Tuple
from chromadb.config import Settings
from config import Config
from llm_interface import LLMFactory

class VectorDatabase:
    def __init__(self, persist_directory: str = None, collection_name: str = "gt_wiki"):
        self.persist_directory = persist_directory or Config.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name
        
        # Create ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection '{collection_name}' with {self.collection.count()} documents")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "GT New Horizons Wiki content"}
            )
            print(f"Created new collection '{collection_name}'")
        
        # Initialize embedding model
        self.embedding_model = LLMFactory.create_embedding_model()
    
    def add_chunks(self, chunks: List[Dict], batch_size: int = 100):
        """Add text chunks to the vector database"""
        print(f"Adding {len(chunks)} chunks to vector database...")
        
        # Process in batches to avoid memory issues
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare batch data
            texts = [chunk['text'] for chunk in batch]
            ids = [f"chunk_{chunk['source_title']}_{chunk['chunk_id']}" for chunk in batch]
            metadatas = []
            
            for chunk in batch:
                metadata = {
                    'source_title': chunk['source_title'],
                    'source_url': chunk['source_url'],
                    'chunk_id': str(chunk['chunk_id']),
                    'tokens': str(chunk['tokens'])
                }
                metadatas.append(metadata)
            
            # Generate embeddings
            print(f"Generating embeddings for batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            embeddings = self.embedding_model.generate_embeddings(texts)
            
            # Add to collection
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Added batch {i//batch_size + 1}, total documents: {self.collection.count()}")
    
    def search(self, query: str, n_results: int = 5, filter_metadata: Dict = None) -> List[Dict]:
        """Search for similar chunks"""
        # Generate query embedding
        query_embedding = self.embedding_model.generate_embeddings([query])[0]
        
        # Prepare search parameters
        search_kwargs = {
            'query_embeddings': [query_embedding],
            'n_results': n_results,
            'include': ['documents', 'metadatas', 'distances']
        }
        
        if filter_metadata:
            search_kwargs['where'] = filter_metadata
        
        # Perform search
        results = self.collection.query(**search_kwargs)
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                result = {
                    'text': results['documents'][0][i],
                    'source_title': results['metadatas'][0][i]['source_title'],
                    'source_url': results['metadatas'][0][i]['source_url'],
                    'chunk_id': results['metadatas'][0][i]['chunk_id'],
                    'tokens': int(results['metadatas'][0][i]['tokens']),
                    'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def search_by_keywords(self, keywords: List[str], n_results: int = 10) -> List[Dict]:
        """Search using keyword matching in addition to vector similarity"""
        # Combine keywords into query
        query = " ".join(keywords)
        
        # Get vector search results
        vector_results = self.search(query, n_results * 2)  # Get more to allow for filtering
        
        # Filter results that contain at least one keyword
        keyword_filtered = []
        for result in vector_results:
            text_lower = result['text'].lower()
            title_lower = result['source_title'].lower()
            
            # Check if any keyword appears in text or title
            keyword_found = any(
                keyword.lower() in text_lower or keyword.lower() in title_lower 
                for keyword in keywords
            )
            
            if keyword_found:
                # Add keyword relevance score
                keyword_matches = sum(
                    1 for keyword in keywords 
                    if keyword.lower() in text_lower or keyword.lower() in title_lower
                )
                result['keyword_relevance'] = keyword_matches / len(keywords)
                keyword_filtered.append(result)
        
        # Sort by combined score (similarity + keyword relevance)
        for result in keyword_filtered:
            result['combined_score'] = (
                result['similarity_score'] * 0.7 + 
                result['keyword_relevance'] * 0.3
            )
        
        keyword_filtered.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return keyword_filtered[:n_results]
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        
        # Get sample of metadata to analyze
        sample_size = min(100, count)
        if count > 0:
            sample = self.collection.peek(limit=sample_size)
            
            # Analyze source distribution
            sources = {}
            total_tokens = 0
            
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    source = metadata['source_title']
                    sources[source] = sources.get(source, 0) + 1
                    total_tokens += int(metadata.get('tokens', 0))
            
            avg_tokens = total_tokens / len(sample['metadatas']) if sample['metadatas'] else 0
            
            return {
                'total_chunks': count,
                'unique_sources_sample': len(sources),
                'avg_tokens_per_chunk': avg_tokens,
                'top_sources': sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        return {'total_chunks': 0}
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.client.delete_collection(name=self.collection_name)
        print(f"Deleted collection '{self.collection_name}'")
    
    def reset_database(self):
        """Reset the database (delete and recreate collection)"""
        try:
            self.delete_collection()
        except:
            pass
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "GT New Horizons Wiki content"}
        )
        print("Reset vector database")

class VectorSearchRanker:
    @staticmethod
    def rank_by_relevance(results: List[Dict], query: str) -> List[Dict]:
        """Rank search results by relevance using multiple criteria"""
        query_words = set(query.lower().split())
        
        for result in results:
            text_words = set(result['text'].lower().split())
            title_words = set(result['source_title'].lower().split())
            
            # Calculate various relevance scores
            text_overlap = len(query_words.intersection(text_words)) / len(query_words) if query_words else 0
            title_overlap = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
            
            # Position-based scoring (earlier matches are better)
            position_score = 0
            text_lower = result['text'].lower()
            for word in query_words:
                pos = text_lower.find(word)
                if pos != -1:
                    # Earlier positions get higher scores
                    position_score += 1.0 / (pos + 1)
            
            # Combine scores
            relevance_score = (
                result['similarity_score'] * 0.4 +
                text_overlap * 0.3 +
                title_overlap * 0.2 +
                min(position_score, 1.0) * 0.1
            )
            
            result['relevance_score'] = relevance_score
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results

if __name__ == "__main__":
    # Test the vector database
    db = VectorDatabase()
    
    # Test with sample data
    sample_chunks = [
        {
            'text': 'The Electric Blast Furnace is a multiblock machine used for smelting.',
            'tokens': 15,
            'source_title': 'Electric Blast Furnace',
            'source_url': 'https://wiki.gtnewhorizons.com/wiki/Electric_Blast_Furnace',
            'chunk_id': 0
        }
    ]
    
    print("Testing vector database...")
    db.add_chunks(sample_chunks)
    
    # Test search
    results = db.search("blast furnace smelting", n_results=3)
    for result in results:
        print(f"Found: {result['source_title']} (similarity: {result['similarity_score']:.3f})")
    
    # Show stats
    stats = db.get_collection_stats()
    print(f"Database stats: {stats}")