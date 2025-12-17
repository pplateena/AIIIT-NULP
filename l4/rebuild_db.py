#!/usr/bin/env python3
"""
Rebuild the database with better quality filters and smaller chunks.
This creates a more accurate, focused database.
"""

import json
import os
from text_processor import TextProcessor
from vector_db import VectorDatabase
from config import Config

class ImprovedTextProcessor(TextProcessor):
    """Enhanced text processor with stricter quality filters"""

    def __init__(self):
        # Balanced chunk size for coverage and accuracy
        super().__init__(chunk_size=600, chunk_overlap=100)

    def is_quality_page(self, page_data: dict) -> bool:
        """Filter out low-quality pages before processing"""
        text = page_data.get('plain_text', '')
        title = page_data.get('title', '')

        # Skip very short pages
        if len(text) < 200:
            return False

        # Skip navigation/template pages
        skip_keywords = [
            'category:', 'template:', 'file:', 'mediawiki:',
            'user:', 'talk:', 'special:', 'help:'
        ]
        if any(kw in title.lower() for kw in skip_keywords):
            return False

        # Skip pages that are mostly lists or tables (high punctuation ratio)
        alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
        if alpha_ratio < 0.5:
            return False

        return True

    def filter_chunks_by_quality(self, chunks: list, min_tokens: int = 50) -> list:
        """Stricter chunk quality filters"""
        quality_chunks = []

        for chunk in chunks:
            text = chunk['text']
            tokens = chunk['tokens']

            # Skip very short chunks
            if tokens < min_tokens:
                continue

            # Skip chunks with too little actual content
            alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
            if alpha_ratio < 0.65:  # Stricter than 0.6
                continue

            # Skip chunks with too many repeated words (copy-paste junk)
            words = text.lower().split()
            if not words:
                continue
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.6:  # Stricter than 0.5
                continue

            # Skip chunks that are mostly short words (might be navigation)
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len < 3.5:
                continue

            quality_chunks.append(chunk)

        return quality_chunks

def rebuild_database(use_cached: bool = True, max_pages: int = None):
    """Rebuild the database with improved quality"""

    print("🔨 Rebuilding database with quality filters...")
    print("=" * 60)

    # Load scraped data
    cached_file = "scraped_wiki_data.json"
    if not os.path.exists(cached_file):
        print(f"❌ Error: {cached_file} not found!")
        print("Run: python main_simple.py build --no-cache")
        return

    with open(cached_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)

    print(f"📚 Loaded {len(scraped_data)} scraped pages")

    # Initialize improved processor
    processor = ImprovedTextProcessor()

    # Filter pages first
    print("\n🔍 Filtering pages...")
    quality_pages = [p for p in scraped_data if processor.is_quality_page(p)]
    print(f"   Kept {len(quality_pages)}/{len(scraped_data)} quality pages")

    if max_pages:
        quality_pages = quality_pages[:max_pages]
        print(f"   Limited to {max_pages} pages")

    # Process into chunks
    print("\n✂️  Creating chunks (600 tokens, 100 overlap)...")
    all_chunks = processor.process_scraped_data(quality_pages)

    # Filter chunks
    print("\n🎯 Filtering chunks...")
    quality_chunks = processor.filter_chunks_by_quality(all_chunks, min_tokens=50)

    if not quality_chunks:
        print("❌ No quality chunks created!")
        return

    # Reset and rebuild database
    print(f"\n💾 Building database with {len(quality_chunks)} chunks...")
    vdb = VectorDatabase()
    vdb.reset_database()
    vdb.add_chunks(quality_chunks)

    # Show stats
    print("\n" + "=" * 60)
    print("✅ Database rebuilt successfully!")
    stats = vdb.get_collection_stats()
    print(f"\n📊 New Statistics:")
    print(f"   Total chunks: {stats.get('total_chunks', 0)}")
    print(f"   Avg tokens/chunk: {stats.get('avg_tokens_per_chunk', 0):.1f}")

    if 'top_sources' in stats:
        print(f"\n📑 Top 10 sources:")
        for source, count in stats['top_sources'][:10]:
            print(f"   • {source}: {count} chunks")

    print("\n💡 Tips:")
    print("   - Medium chunks (600) = balance of coverage & precision")
    print("   - Uses 5 chunks with full text (no truncation)")
    print("   - Test with: python main_simple.py ask")

if __name__ == "__main__":
    import sys

    max_pages = None
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
            print(f"Limiting to {max_pages} pages")
        except:
            print(f"Usage: python rebuild_db.py [max_pages]")
            print(f"Example: python rebuild_db.py 50  # Use only 50 best pages")
            sys.exit(1)

    rebuild_database(max_pages=max_pages)
