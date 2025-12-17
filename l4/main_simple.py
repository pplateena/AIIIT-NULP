#!/usr/bin/env python3
import click
import os
import sys
from rag_pipeline import RAGPipeline
from config import Config
from markdown_renderer import render_markdown

@click.group()
@click.option('--llm-provider', type=click.Choice(['claude', 'gemini', 'ollama']),
              default=Config.DEFAULT_LLM_PROVIDER,
              help='LLM provider to use (claude, gemini, or ollama for local)')
@click.pass_context
def cli(ctx, llm_provider):
    """GT New Horizons Wiki RAG System"""
    ctx.ensure_object(dict)
    ctx.obj['llm_provider'] = llm_provider

@cli.command()
@click.option('--max-pages', type=int, default=None,
              help='Maximum number of pages to scrape (default: all pages)')
@click.option('--reset-db', is_flag=True,
              help='Reset the vector database before building')
@click.option('--no-cache', is_flag=True,
              help='Do not use cached scraped data')
@click.pass_context
def build(ctx, max_pages, reset_db, no_cache):
    """Build the knowledge base from wiki data"""
    print(f"Building knowledge base with {ctx.obj['llm_provider']} LLM...")
    
    if reset_db:
        print("Resetting vector database...")
    
    rag = RAGPipeline(llm_provider=ctx.obj['llm_provider'], reset_db=reset_db)
    
    try:
        use_cached = not no_cache
        rag.build_knowledge_base(max_pages=max_pages, use_cached=use_cached)
        
        # Show final stats
        stats = rag.vector_db.get_collection_stats()
        print(f"\nKnowledge base built successfully!")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Average tokens per chunk: {stats.get('avg_tokens_per_chunk', 0):.1f}")
        
    except Exception as e:
        print(f"Error building knowledge base: {e}")
        sys.exit(1)

@cli.command()
@click.option('--question', '-q', help='Single question to ask')
@click.option('--no-history', is_flag=True, help='Disable dialogue history')
@click.pass_context
def ask(ctx, question, no_history):
    """Ask a question or start interactive session"""
    rag = RAGPipeline(llm_provider=ctx.obj['llm_provider'])
    
    # Check if knowledge base exists
    stats = rag.vector_db.get_collection_stats()
    if stats.get('total_chunks', 0) == 0:
        print("Knowledge base is empty! Run 'python main_simple.py build' first.")
        sys.exit(1)
    
    if question:
        # Single question mode
        print(f"Searching for: {question}")
        response, sources = rag.generate_response(question, use_history=not no_history)
        
        print(f"\nAnswer:")
        print(render_markdown(response))
        
        if sources:
            print(f"\nSources ({len(sources)} found):")
            for i, source in enumerate(sources, 1):
                print(f"  {i}. {source['title']} (relevance: {source['relevance_score']:.3f})")
                print(f"     Link: {source['url']}")
                print()
    else:
        # Interactive mode
        rag.interactive_session()

@cli.command()
def stats():
    """Show knowledge base statistics"""
    rag = RAGPipeline()
    stats = rag.vector_db.get_collection_stats()
    
    print("Knowledge Base Statistics:")
    print(f"   Total chunks: {stats.get('total_chunks', 0)}")
    if stats.get('total_chunks', 0) > 0:
        print(f"   Average tokens per chunk: {stats.get('avg_tokens_per_chunk', 0):.1f}")
        
        if 'top_sources' in stats:
            print("   Top source pages:")
            for source, count in stats['top_sources']:
                print(f"     - {source}: {count} chunks")

@cli.command()
def test_scraper():
    """Test the wiki scraper with a small sample"""
    from wiki_scraper import WikiScraper
    
    print("Testing wiki scraper...")
    scraper = WikiScraper()
    
    # Test with just 3 pages
    data = scraper.scrape_wiki(max_pages=3)
    
    if data:
        print(f"Successfully scraped {len(data)} pages:")
        for page in data:
            print(f"  - {page['title']}: {len(page['plain_text'])} characters")
        
        scraper.save_scraped_data("test_data.json")
        print("Test data saved to test_data.json")
    else:
        print("No data scraped. Check network connection or try different pages.")

@cli.command()
@click.pass_context
def voice(ctx):
    """Start voice-enabled interactive mode"""
    try:
        from voice_interface import VoiceEnabledRAG
        
        print("Initializing voice-enabled RAG system...")
        rag = RAGPipeline(llm_provider=ctx.obj['llm_provider'])
        
        # Check if knowledge base exists
        stats = rag.vector_db.get_collection_stats()
        if stats.get('total_chunks', 0) == 0:
            print("Knowledge base is empty! Run 'python main_simple.py build' first.")
            sys.exit(1)
        
        voice_rag = VoiceEnabledRAG(rag)
        voice_rag.start_voice_mode()
        
    except ImportError as e:
        print("Voice dependencies not installed. Install with:")
        print("pip install SpeechRecognition pyttsx3 pyaudio")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Voice mode error: {e}")
        sys.exit(1)

@cli.command()
def test_voice():
    """Test voice system components"""
    try:
        from voice_interface import VoiceInterface
        
        voice = VoiceInterface()
        voice.test_voice_system()
        
    except ImportError as e:
        print("Voice dependencies not installed. Install with:")
        print("pip install SpeechRecognition pyttsx3 pyaudio")
        print(f"Error: {e}")
    except Exception as e:
        print(f"Voice test error: {e}")

if __name__ == '__main__':
    cli()