"""
Simplified prompts for local models like Ollama
Local models need simpler, more direct prompts
"""

def get_simple_rag_prompt(question: str, context_chunks: list) -> str:
    """Simple prompt format that works better with local models"""

    prompt = "You are a helpful assistant answering questions about GT New Horizons Minecraft modpack.\n\n"

    prompt += "Context information:\n"
    for i, chunk in enumerate(context_chunks[:3], 1):  # Limit to top 3 chunks
        prompt += f"\n[Source {i}]: {chunk['text'][:400]}\n"  # Limit text length

    prompt += f"\n\nQuestion: {question}\n\n"
    prompt += "Answer the question using ONLY the context information above. Keep your answer concise and factual.\n\n"
    prompt += "Answer:"

    return prompt
