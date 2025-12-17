import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import Config
from wiki_scraper import WikiScraper
from text_processor import TextProcessor
from vector_db import VectorDatabase, VectorSearchRanker
from llm_interface import LLMFactory, RAGPromptTemplate
from markdown_renderer import render_markdown

class DialogueHistory:
    def __init__(self, filename: str = None):
        self.filename = filename or Config.DIALOGUE_HISTORY_FILE
        self.history = self.load_history()
    
    def load_history(self) -> List[Dict]:
        """Load dialogue history from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
        return []
    
    def save_history(self):
        """Save dialogue history to file"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_exchange(self, user_query: str, assistant_response: str, sources: List[Dict]):
        """Add a new dialogue exchange"""
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user': user_query,
            'assistant': assistant_response,
            'sources': sources
        }
        self.history.append(exchange)
        self.save_history()
    
    def get_recent_history(self, n: int = 3) -> List[Dict]:
        """Get the n most recent exchanges"""
        return self.history[-n:] if self.history else []
    
    def clear_history(self):
        """Clear all history"""
        self.history = []
        self.save_history()

class RAGPipeline:
    def __init__(self, llm_provider: str = None, reset_db: bool = False):
        """Initialize RAG pipeline"""
        # Initialize components
        self.llm = LLMFactory.create_llm(llm_provider)
        self.vector_db = VectorDatabase()
        self.text_processor = TextProcessor()
        self.dialogue_history = DialogueHistory()
        self.ranker = VectorSearchRanker()
        
        # Reset database if requested
        if reset_db:
            self.vector_db.reset_database()
        
        print(f"RAG Pipeline initialized with {llm_provider or Config.DEFAULT_LLM_PROVIDER} LLM")
        print(f"Vector DB stats: {self.vector_db.get_collection_stats()}")
    
    def build_knowledge_base(self, max_pages: int = None, use_cached: bool = True):
        """Build the knowledge base from wiki data"""
        scraper = WikiScraper()
        
        # Try to load cached data first
        cached_file = "scraped_wiki_data.json"
        if use_cached and os.path.exists(cached_file):
            print("Loading cached wiki data...")
            scraped_data = scraper.load_scraped_data(cached_file)
        else:
            print("Scraping wiki data...")
            scraped_data = scraper.scrape_wiki(max_pages=max_pages)
            scraper.save_scraped_data(cached_file)
        
        if not scraped_data:
            print("No wiki data available!")
            return
        
        # Process text into chunks
        print("Processing text into chunks...")
        chunks = self.text_processor.process_scraped_data(scraped_data)
        
        # Filter chunks for quality
        quality_chunks = self.text_processor.filter_chunks_by_quality(chunks)
        
        # Add to vector database
        if quality_chunks:
            print("Adding chunks to vector database...")
            self.vector_db.add_chunks(quality_chunks)
            print(f"Knowledge base built with {len(quality_chunks)} chunks")
        else:
            print("No quality chunks generated!")
    
    def extract_search_keywords(self, question: str) -> List[str]:
        """Extract search keywords from question using LLM"""
        prompt = RAGPromptTemplate.get_search_query_prompt(question)
        
        try:
            response = self.llm.generate_response(prompt)
            # Extract keywords from response
            keywords = []
            for line in response.split('\n'):
                line = line.strip()
                if line and not line.startswith(('Keywords:', 'Key terms:', 'Search:')):
                    # Split on common delimiters and clean
                    words = line.replace(',', ' ').replace(';', ' ').split()
                    keywords.extend([w.strip().lower() for w in words if w.strip()])
            
            return list(set(keywords)) if keywords else [question.lower()]
        
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback to simple word extraction
            return question.lower().split()
    
    def search_relevant_context(self, question: str, n_results: int = 10) -> List[Dict]:
        """Search for relevant context using both vector similarity and keywords"""
        # Extract keywords
        keywords = self.extract_search_keywords(question)
        
        # Search using keywords
        keyword_results = self.vector_db.search_by_keywords(keywords, n_results * 2)
        
        # Also do direct vector search
        vector_results = self.vector_db.search(question, n_results)
        
        # Combine and deduplicate results
        all_results = {}
        for result in keyword_results + vector_results:
            key = f"{result['source_title']}_{result['chunk_id']}"
            if key not in all_results:
                all_results[key] = result
        
        # Rank results
        ranked_results = self.ranker.rank_by_relevance(list(all_results.values()), question)
        
        return ranked_results[:n_results]
    
    def generate_response(self, question: str, use_history: bool = True) -> Tuple[str, List[Dict]]:
        """Generate response using RAG pipeline"""
        # Search for relevant context
        context_chunks = self.search_relevant_context(question)

        if not context_chunks:
            response = "I couldn't find any relevant information in the GT New Horizons wiki to answer your question."
            return response, []

        # Check if using Ollama (local model) - use simpler prompts
        is_ollama = hasattr(self.llm, '__class__') and 'Ollama' in self.llm.__class__.__name__

        if is_ollama:
            # Simple prompt for local models - anti-hallucination focused
            system_prompt = """You are a factual assistant. Answer ONLY using the provided context. If the context doesn't contain the answer, say "I don't have that information in the wiki context." Do NOT make up information."""

            prompt = f"""Context from GT New Horizons wiki:

"""
            for i, chunk in enumerate(context_chunks[:5], 1):  # Use 5 chunks instead of 3
                prompt += f"[Source {i}] {chunk['text']}\n\n"  # Full text, no truncation

            prompt += f"""Question: {question}

Instructions:
- Answer using ONLY the context above
- Be specific and factual
- If unsure, say you don't know
- Keep answer concise (2-3 sentences)

Answer:"""

            try:
                response = self.llm.generate_response(prompt, system_prompt)
            except Exception as e:
                response = f"Error: {str(e)}"
        else:
            # Complex prompt for cloud models (Gemini/Claude)
            history = self.dialogue_history.get_recent_history() if use_history else None
            system_prompt = RAGPromptTemplate.get_system_prompt()
            user_prompt = RAGPromptTemplate.format_rag_prompt(question, context_chunks, history)

            try:
                response = self.llm.generate_response(user_prompt, system_prompt)
            except Exception as e:
                response = f"Error generating response: {str(e)}"
        
        # Prepare source information
        sources = []
        for chunk in context_chunks:
            source_info = {
                'title': chunk['source_title'],
                'url': chunk['source_url'],
                'relevance_score': chunk.get('relevance_score', chunk.get('similarity_score', 0)),
                'preview': chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
            }
            sources.append(source_info)
        
        # Add to dialogue history
        self.dialogue_history.add_exchange(question, response, sources)
        
        return response, sources
    
    def interactive_session(self):
        """Run an interactive Q&A session"""
        print("\n🤖 GT New Horizons Wiki Assistant")
        print("Ask me anything about the GT New Horizons modpack!")
        print("Type 'quit', 'exit', or 'q' to end the session.")
        print("Type 'history' to see recent conversations.")
        print("Type 'stats' to see knowledge base statistics.")
        print("-" * 60)
        
        while True:
            try:
                question = input("\n💬 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif question.lower() == 'history':
                    self.show_history()
                    continue
                
                elif question.lower() == 'stats':
                    self.show_stats()
                    continue
                
                elif not question:
                    continue
                
                print("\n🔍 Searching for relevant information...")
                response, sources = self.generate_response(question)
                
                print(f"\nAssistant:")
                print(render_markdown(response))
                
                if sources:
                    print(f"\n📚 Sources ({len(sources)} found):")
                    for i, source in enumerate(sources, 1):
                        print(f"  {i}. {source['title']} (relevance: {source['relevance_score']:.3f})")
                        print(f"     {source['url']}")
                        if len(sources) <= 3:  # Show preview for top sources
                            print(f"     Preview: {source['preview']}")
                        print()
            
            except KeyboardInterrupt:
                print("\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def show_history(self):
        """Show recent dialogue history"""
        recent = self.dialogue_history.get_recent_history(5)
        if not recent:
            print("📭 No conversation history found.")
            return
        
        print(f"\n📜 Recent conversations ({len(recent)} entries):")
        for i, exchange in enumerate(recent, 1):
            timestamp = exchange['timestamp'][:19]  # Remove microseconds
            print(f"\n{i}. [{timestamp}]")
            print(f"   User: {exchange['user']}")
            print(f"   Assistant: {exchange['assistant'][:100]}...")
            if exchange['sources']:
                print(f"   Sources: {len(exchange['sources'])} documents")
    
    def show_stats(self):
        """Show knowledge base statistics"""
        stats = self.vector_db.get_collection_stats()
        print("\n📊 Knowledge Base Statistics:")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Average tokens per chunk: {stats.get('avg_tokens_per_chunk', 0):.1f}")
        
        if 'top_sources' in stats:
            print("   Top source pages:")
            for source, count in stats['top_sources']:
                print(f"     • {source}: {count} chunks")

if __name__ == "__main__":
    # Example usage
    rag = RAGPipeline(llm_provider='gemini')
    
    # Build knowledge base if it's empty
    stats = rag.vector_db.get_collection_stats()
    if stats['total_chunks'] == 0:
        print("Knowledge base is empty. Building from wiki data...")
        rag.build_knowledge_base(max_pages=50)  # Start with 50 pages for testing
    
    # Run interactive session
    rag.interactive_session()