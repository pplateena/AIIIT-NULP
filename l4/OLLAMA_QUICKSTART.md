# Ollama Quick Start Guide

## Step 1: Install Ollama

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

## Step 2: Start Ollama Server

```bash
# In a separate terminal window (keep this running)
ollama serve

# Or run as systemd service
sudo systemctl start ollama
sudo systemctl enable ollama  # Auto-start on boot
```

## Step 3: Download a Model

```bash
# Recommended: phi3 (fast, 3.8GB)
ollama pull phi3

# Or other options:
# ollama pull llama3.2    # Balanced (4.7GB)
# ollama pull mistral     # Better quality (7.4GB)
```

## Step 4: Test Ollama

```bash
# Quick test
ollama run phi3 "What is a RAG system?"

# List installed models
ollama list
```

## Step 5: Run Your RAG System

```bash
cd ~/Projects/git-cloned/AIIIT-NULP/l4

# The .env file is already configured to use Ollama!
# Just run your tests:

# Quick test (5 questions)
python quick_test.py

# Full test (21 questions) - NO QUOTA LIMITS!
python test_rag_resumable.py

# Interactive mode
python main_simple.py ask

# Voice mode
python main_simple.py voice
```

## Troubleshooting

### "Connection Error: Cannot connect to Ollama server"

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# If not, start it:
ollama serve

# In another terminal, try again:
python quick_test.py
```

### "Model not found"

**Solution:**
```bash
# Pull the model first
ollama pull phi3

# Verify it's installed
ollama list
```

### "Too slow"

**Solutions:**
```bash
# 1. Use a smaller model
ollama pull phi3:mini

# Update .env
# OLLAMA_MODEL=phi3:mini

# 2. Close other applications to free RAM

# 3. Reduce max tokens in llm_interface.py
# "num_predict": 256  # Instead of 512
```

## Performance Expectations

| Model | Speed (CPU) | Speed (GPU) | Quality |
|-------|-------------|-------------|---------|
| phi3 | ~5-10 sec | ~1-2 sec | Good |
| llama3.2 | ~8-15 sec | ~2-3 sec | Better |
| mistral | ~10-20 sec | ~2-4 sec | Best |

## Switching Between Providers

Edit `.env` file:

```bash
# For Ollama (local, unlimited)
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_MODEL=phi3

# For Gemini (cloud, limited)
DEFAULT_LLM_PROVIDER=gemini

# For Claude (cloud, limited)
DEFAULT_LLM_PROVIDER=claude
```

Or use command-line:
```bash
# Force use Ollama
python main_simple.py --llm-provider ollama ask

# Force use Gemini
python main_simple.py --llm-provider gemini ask
```

## Benefits of Using Ollama

✅ **Unlimited requests** - Test as much as you want
✅ **No API costs** - Completely free
✅ **Works offline** - No internet needed
✅ **Privacy** - Data stays on your computer
✅ **No quotas** - Run 1000+ tests if you want

## Next Steps

1. **Run full test suite:**
   ```bash
   python test_rag_resumable.py --llm-provider ollama
   ```

2. **Compare with Gemini:**
   ```bash
   # Save Ollama results
   python test_rag_resumable.py --llm-provider ollama

   # Save Gemini results (when quota resets)
   python test_rag_resumable.py --llm-provider gemini

   # Compare in your report!
   ```

3. **Use for development:**
   - Ollama for debugging and testing
   - Gemini/Claude for final quality check
