#!/usr/bin/env python3
import click
import os
import sys
from rag_pipeline import RAGPipeline
from config import Config

@click.group()
@click.option('--llm-provider', type=click.Choice(['claude', 'gemini']), 
              default=Config.DEFAULT_LLM_PROVIDER,
              help='LLM provider to use (claude or gemini)')
@click.pass_context
def cli(ctx, llm_provider):
    """GT New Horizons Wiki RAG System
    
    A Retrieval-Augmented Generation system for querying the GT New Horizons modpack wiki.
    """
    ctx.ensure_object(dict)
    ctx.obj['llm_provider'] = llm_provider

@cli.command()
@click.option('--max-pages', type=int, default=None,
              help='Maximum number of pages to scrape (default: all pages)')
@click.option('--reset-db', is_flag=True,
              help='Reset the vector database before building')
@click.option('--use-cached', is_flag=True, default=True,
              help='Use cached scraped data if available')
@click.pass_context
def build(ctx, max_pages, reset_db, use_cached):
    """Build the knowledge base from wiki data"""
    click.echo(f"🔨 Building knowledge base with {ctx.obj['llm_provider']} LLM...")
    
    if reset_db:
        click.echo("🗑️ Resetting vector database...")
    
    rag = RAGPipeline(llm_provider=ctx.obj['llm_provider'], reset_db=reset_db)
    
    try:
        rag.build_knowledge_base(max_pages=max_pages, use_cached=use_cached)
        
        # Show final stats
        stats = rag.vector_db.get_collection_stats()
        click.echo(f"\n✅ Knowledge base built successfully!")
        click.echo(f"   Total chunks: {stats.get('total_chunks', 0)}")
        click.echo(f"   Average tokens per chunk: {stats.get('avg_tokens_per_chunk', 0):.1f}")
        
    except Exception as e:
        click.echo(f"❌ Error building knowledge base: {e}")
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
        click.echo("❌ Knowledge base is empty! Run 'python main.py build' first.")
        sys.exit(1)
    
    if question:
        # Single question mode
        click.echo(f"🔍 Searching for: {question}")
        response, sources = rag.generate_response(question, use_history=not no_history)
        
        click.echo(f"\n🤖 Answer:\n{response}")
        
        if sources:
            click.echo(f"\n📚 Sources ({len(sources)} found):")
            for i, source in enumerate(sources, 1):
                click.echo(f"  {i}. {source['title']} (relevance: {source['relevance_score']:.3f})")
                click.echo(f"     🔗 {source['url']}")
                click.echo()
    else:
        # Interactive mode
        rag.interactive_session()

@cli.command()
def stats():
    """Show knowledge base statistics"""
    rag = RAGPipeline()
    stats = rag.vector_db.get_collection_stats()
    
    click.echo("📊 Knowledge Base Statistics:")
    click.echo(f"   Total chunks: {stats.get('total_chunks', 0)}")
    if stats.get('total_chunks', 0) > 0:
        click.echo(f"   Average tokens per chunk: {stats.get('avg_tokens_per_chunk', 0):.1f}")
        
        if 'top_sources' in stats:
            click.echo("   Top source pages:")
            for source, count in stats['top_sources']:
                click.echo(f"     • {source}: {count} chunks")

@cli.command()
@click.option('--last', '-n', type=int, default=10, help='Number of recent exchanges to show')
def history(last):
    """Show dialogue history"""
    from rag_pipeline import DialogueHistory
    
    dialogue_history = DialogueHistory()
    recent = dialogue_history.get_recent_history(last)
    
    if not recent:
        click.echo("📭 No conversation history found.")
        return
    
    click.echo(f"📜 Recent conversations ({len(recent)} entries):")
    for i, exchange in enumerate(recent, 1):
        timestamp = exchange['timestamp'][:19]  # Remove microseconds
        click.echo(f"\n{i}. [{timestamp}]")
        click.echo(f"   ❓ User: {exchange['user']}")
        click.echo(f"   🤖 Assistant: {exchange['assistant'][:200]}{'...' if len(exchange['assistant']) > 200 else ''}")
        if exchange['sources']:
            click.echo(f"   📚 Sources: {len(exchange['sources'])} documents")

@cli.command()
def clear_history():
    """Clear all dialogue history"""
    from rag_pipeline import DialogueHistory
    
    if click.confirm('Are you sure you want to clear all dialogue history?'):
        dialogue_history = DialogueHistory()
        dialogue_history.clear_history()
        click.echo("🗑️ Dialogue history cleared.")

@cli.command()
@click.option('--output', '-o', default='test_questions.txt', help='Output file for test questions')
def generate_test_questions(output):
    """Generate test questions for evaluation"""
    rag = RAGPipeline()
    
    # Check if knowledge base exists
    stats = rag.vector_db.get_collection_stats()
    if stats.get('total_chunks', 0) == 0:
        click.echo("❌ Knowledge base is empty! Run 'python main.py build' first.")
        sys.exit(1)
    
    # Sample test questions for GT New Horizons
    test_questions = [
        "How do I build an Electric Blast Furnace?",
        "What materials do I need for LV tier machines?",
        "How does the GT New Horizons progression work?",
        "What is the difference between LV, MV, and HV power tiers?",
        "How do I process ores efficiently in early game?",
        "What are the requirements for entering the HV tier?",
        "How do I set up automated ore processing?",
        "What machines do I need for chemical processing?",
        "How does the GT power system work?",
        "What are the best early game power sources?",
        "How do I make steel in GT New Horizons?",
        "What is the purpose of the Research Station?",
        "How do I unlock higher tier recipes?",
        "What are the different types of cables and their uses?",
        "How do I troubleshoot machine automation issues?"
    ]
    
    click.echo(f"📝 Generating {len(test_questions)} test questions...")
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write("GT New Horizons RAG System Test Questions\n")
        f.write("=" * 50 + "\n\n")
        
        for i, question in enumerate(test_questions, 1):
            f.write(f"{i}. {question}\n")
        
        f.write(f"\nGenerated {len(test_questions)} test questions for evaluation.\n")
    
    click.echo(f"✅ Test questions saved to {output}")

@cli.command()
@click.option('--input-file', '-i', default='test_questions.txt', help='File with test questions')
@click.option('--output', '-o', default='evaluation_results.json', help='Output file for results')
@click.pass_context
def evaluate(ctx, input_file, output):
    """Evaluate the system with test questions"""
    import json
    from datetime import datetime
    
    if not os.path.exists(input_file):
        click.echo(f"❌ Input file {input_file} not found. Run 'generate-test-questions' first.")
        sys.exit(1)
    
    rag = RAGPipeline(llm_provider=ctx.obj['llm_provider'])
    
    # Read test questions
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    questions = []
    for line in lines:
        line = line.strip()
        if line and line[0].isdigit() and '.' in line:
            question = line.split('.', 1)[1].strip()
            questions.append(question)
    
    click.echo(f"📋 Found {len(questions)} test questions")
    click.echo("🧪 Running evaluation...")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'llm_provider': ctx.obj['llm_provider'],
        'total_questions': len(questions),
        'results': []
    }
    
    for i, question in enumerate(questions, 1):
        click.echo(f"   Question {i}/{len(questions)}: {question[:50]}...")
        
        try:
            response, sources = rag.generate_response(question, use_history=False)
            
            result = {
                'question': question,
                'response': response,
                'num_sources': len(sources),
                'sources': [{'title': s['title'], 'url': s['url'], 'relevance': s['relevance_score']} for s in sources],
                'response_length': len(response.split()),
                'success': True
            }
            
        except Exception as e:
            result = {
                'question': question,
                'response': f"Error: {str(e)}",
                'num_sources': 0,
                'sources': [],
                'response_length': 0,
                'success': False
            }
        
        results['results'].append(result)
    
    # Save results
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    successful = sum(1 for r in results['results'] if r['success'])
    avg_sources = sum(r['num_sources'] for r in results['results']) / len(results['results'])
    avg_response_length = sum(r['response_length'] for r in results['results']) / len(results['results'])
    
    click.echo(f"\n📊 Evaluation Results:")
    click.echo(f"   Successful responses: {successful}/{len(questions)} ({successful/len(questions)*100:.1f}%)")
    click.echo(f"   Average sources per response: {avg_sources:.1f}")
    click.echo(f"   Average response length: {avg_response_length:.1f} words")
    click.echo(f"   Results saved to: {output}")

@cli.command()
def setup():
    """Setup the system with initial configuration"""
    click.echo("🚀 Setting up GT New Horizons RAG System...")
    
    # Check for API keys
    env_file = ".env"
    if not os.path.exists(env_file):
        click.echo("📝 Creating .env file from template...")
        with open(".env.example", 'r') as src, open(".env", 'w') as dst:
            dst.write(src.read())
        click.echo(f"✅ Created {env_file}. Please edit it with your API keys.")
    
    # Check API keys
    from config import Config
    
    missing_keys = []
    if not Config.ANTHROPIC_API_KEY:
        missing_keys.append("ANTHROPIC_API_KEY")
    if not Config.GOOGLE_API_KEY:
        missing_keys.append("GOOGLE_API_KEY")
    
    if missing_keys:
        click.echo(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        click.echo(f"   Please edit {env_file} and add your API keys.")
        click.echo("   You can get them from:")
        click.echo("   - Anthropic: https://console.anthropic.com/")
        click.echo("   - Google: https://aistudio.google.com/")
        return
    
    click.echo("✅ API keys found!")
    
    # Test LLM connection
    try:
        rag = RAGPipeline(llm_provider=Config.DEFAULT_LLM_PROVIDER)
        click.echo(f"✅ {Config.DEFAULT_LLM_PROVIDER.title()} LLM connection successful!")
    except Exception as e:
        click.echo(f"❌ LLM connection failed: {e}")
        return
    
    click.echo("\n🎯 Next steps:")
    click.echo("   1. Run 'python main.py build' to create the knowledge base")
    click.echo("   2. Run 'python main.py ask' to start asking questions")

if __name__ == '__main__':
    cli()