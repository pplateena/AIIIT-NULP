# GT New Horizons Wiki RAG System

A Retrieval-Augmented Generation (RAG) system for querying the GT New Horizons Minecraft modpack wiki. This system scrapes wiki content, creates a searchable vector database, and provides intelligent answers with source citations.

## Features

- 🕷️ **Wiki Scraping**: Automatically extracts content from GT New Horizons wiki
- 🧠 **Smart Chunking**: Intelligent text preprocessing with configurable chunk sizes and overlap
- 🔍 **Hybrid Search**: Combines vector similarity and keyword matching for better results
- 🤖 **Multi-LLM Support**: Choose between Claude and Gemini models
- 📚 **Source Citation**: All answers include links to original wiki pages
- 💬 **Dialogue History**: Maintains conversation context
- 🎯 **Relevance Ranking**: Advanced scoring system for result quality
- 🛠️ **CLI Interface**: Easy-to-use command line interface

## Installation

1. **Clone and navigate to the project:**
   ```bash
   cd l4/
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup configuration:**
   ```bash
   python main.py setup
   ```

4. **Configure API keys in `.env`:**
   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   ```

## Quick Start

### 1. Build Knowledge Base
```bash
# Build from all wiki pages
python main.py build

# Build from limited pages (for testing)
python main.py build --max-pages 50

# Reset database and rebuild
python main.py build --reset-db
```

### 2. Ask Questions
```bash
# Interactive mode
python main.py ask

# Single question
python main.py ask -q "How do I build an Electric Blast Furnace?"

# Use Claude instead of default Gemini
python main.py --llm-provider claude ask
```

### 3. View Statistics
```bash
# Knowledge base stats
python main.py stats

# Conversation history
python main.py history
```

## CLI Commands

### Main Commands

| Command | Description | Options |
|---------|-------------|---------|
| `build` | Build knowledge base from wiki | `--max-pages`, `--reset-db`, `--use-cached` |
| `ask` | Ask questions (interactive or single) | `--question`, `--no-history` |
| `stats` | Show knowledge base statistics | - |
| `history` | View dialogue history | `--last` |
| `setup` | Initial system setup | - |

### Evaluation Commands

| Command | Description | Options |
|---------|-------------|---------|
| `generate-test-questions` | Create test question file | `--output` |
| `evaluate` | Run evaluation on test questions | `--input-file`, `--output` |
| `clear-history` | Clear all dialogue history | - |

### Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--llm-provider` | Choose LLM (claude/gemini) | gemini |

## Configuration

Edit `.env` file to customize:

```env
# API Keys
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Model Settings
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Processing Settings
CHUNK_SIZE=800
CHUNK_OVERLAP=200
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## Architecture

### Components

1. **Wiki Scraper** (`wiki_scraper.py`)
   - Fetches all pages from GT New Horizons wiki
   - Converts MediaWiki markup to clean text
   - Handles rate limiting and error recovery

2. **Text Processor** (`text_processor.py`)
   - Cleans and normalizes text content
   - Creates overlapping chunks for better context
   - Filters low-quality content

3. **Vector Database** (`vector_db.py`)
   - ChromaDB for persistent vector storage
   - Hybrid search (vector + keyword)
   - Relevance scoring and ranking

4. **LLM Interface** (`llm_interface.py`)
   - Configurable support for Claude and Gemini
   - Consistent API across providers
   - Fallback embedding models

5. **RAG Pipeline** (`rag_pipeline.py`)
   - Orchestrates the entire RAG workflow
   - Manages dialogue history
   - Handles context retrieval and response generation

### Data Flow

```
Wiki Pages → Scraper → Text Processor → Vector DB
                                           ↓
User Question → Search → Context Retrieval → LLM → Response + Sources
```

## Usage Examples

### Interactive Session
```bash
$ python main.py ask

🤖 GT New Horizons Wiki Assistant
Ask me anything about the GT New Horizons modpack!
Type 'quit', 'exit', or 'q' to end the session.

💬 Your question: How do I make steel?

🔍 Searching for relevant information...

🤖 Assistant: To make steel in GT New Horizons, you need to use an Electric Blast Furnace (EBF). Here's the process:

1. **Build an Electric Blast Furnace**: You'll need heating coils and a proper multiblock structure
2. **Input Materials**: Iron ingots + carbon (from coal/charcoal)
3. **Heat Requirement**: Steel requires 1000K+ temperature
4. **Recipe**: 1 Iron + 1 Carbon → 1 Steel (in EBF)

📚 Sources (3 found):
  1. Electric Blast Furnace (relevance: 0.892)
     https://wiki.gtnewhorizons.com/wiki/Electric_Blast_Furnace
  
  2. Steel Production (relevance: 0.845)
     https://wiki.gtnewhorizons.com/wiki/Steel
```

### Single Question
```bash
$ python main.py ask -q "What power tier comes after LV?"

🔍 Searching for: What power tier comes after LV?

🤖 Answer:
After LV (Low Voltage), the next power tier is MV (Medium Voltage). The GT New Horizons power progression follows this sequence:
- ULV (Ultra Low Voltage)
- LV (Low Voltage) 
- MV (Medium Voltage)
- HV (High Voltage)
- EV (Extreme Voltage)
- And so on...

📚 Sources (2 found):
  1. Power Tiers (relevance: 0.934)
     🔗 https://wiki.gtnewhorizons.com/wiki/Power_Tiers
```

### Using Claude Instead of Gemini
```bash
$ python main.py --llm-provider claude ask -q "Explain ore processing"
```

## Evaluation

### Generate Test Questions
```bash
$ python main.py generate-test-questions
📝 Generating 15 test questions...
✅ Test questions saved to test_questions.txt
```

### Run Evaluation
```bash
$ python main.py evaluate
📋 Found 15 test questions
🧪 Running evaluation...
   Question 1/15: How do I build an Electric Blast Furnace?...
   Question 2/15: What materials do I need for LV tier machines?...
   ...

📊 Evaluation Results:
   Successful responses: 15/15 (100.0%)
   Average sources per response: 3.2
   Average response length: 87.3 words
   Results saved to: evaluation_results.json
```

## File Structure

```
l4/
├── main.py                 # CLI interface
├── config.py              # Configuration management
├── wiki_scraper.py        # Wiki content extraction
├── text_processor.py      # Text preprocessing and chunking
├── vector_db.py           # Vector database operations
├── llm_interface.py       # LLM abstraction layer
├── rag_pipeline.py        # Main RAG orchestration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── README_RAG_SYSTEM.md  # This file
└── data/                 # Generated data files
    ├── scraped_wiki_data.json
    ├── dialogue_history.json
    └── chroma_db/        # Vector database files
```

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   ❌ Missing API keys: ANTHROPIC_API_KEY
   ```
   **Solution**: Edit `.env` file with your API keys

2. **Empty Knowledge Base**
   ```bash
   ❌ Knowledge base is empty! Run 'python main.py build' first.
   ```
   **Solution**: Run `python main.py build` to scrape wiki data

3. **Rate Limiting**
   - The scraper includes built-in rate limiting
   - Increase delays if you get blocked

4. **Memory Issues**
   - Reduce `--max-pages` when building
   - Adjust `CHUNK_SIZE` in configuration

### Performance Tips

- **Use cached data**: The scraper saves data to avoid re-scraping
- **Start small**: Use `--max-pages 50` for initial testing
- **Monitor stats**: Use `python main.py stats` to check system health

## API Key Setup

### Anthropic Claude
1. Visit https://console.anthropic.com/
2. Create account and get API key
3. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

### Google Gemini
1. Visit https://aistudio.google.com/
2. Create project and enable API
3. Add to `.env`: `GOOGLE_API_KEY=your_key_here`

## Laboratory Requirements Compliance

This system fulfills all requirements from Laboratory Work #4:

✅ **Task 1**: Theoretical understanding implemented
✅ **Task 2**: Document corpus (GT New Horizons wiki)  
✅ **Task 3**: Text preprocessing and chunking
✅ **Task 4**: Vector database (ChromaDB)
✅ **Task 5**: Vector embeddings storage
✅ **Task 6**: Top-k search implementation
✅ **Task 7**: LLM integration (Claude/Gemini)
✅ **Task 8**: Complete RAG pipeline
✅ **Task 9**: Dialogue history storage
✅ **Task 10**: Relevance ranking system
✅ **Task 11**: Evaluation framework with test questions

## License

Educational project for AI/ML coursework.