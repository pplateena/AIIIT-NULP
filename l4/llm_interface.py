import os
import anthropic
import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from config import Config

class LLMInterface(ABC):
    """Abstract base class for LLM interfaces"""
    
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        pass
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass

class ClaudeLLM(LLMInterface):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Please set ANTHROPIC_API_KEY in .env file")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "max_tokens": 2048,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        
        except Exception as e:
            print(f"Error generating Claude response: {e}")
            return f"Error: {str(e)}"
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Claude doesn't have built-in embeddings, use sentence transformers as fallback
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(Config.DEFAULT_EMBEDDING_MODEL)
        embeddings = model.encode(texts)
        return embeddings.tolist()

class GeminiLLM(LLMInterface):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.embedding_model = genai.GenerativeModel('embedding-001')
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2048,
                    temperature=0.7
                )
            )
            return response.text
        
        except Exception as e:
            print(f"Error generating Gemini response: {e}")
            return f"Error: {str(e)}"
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            return embeddings
        except Exception as e:
            print(f"Error generating Gemini embeddings: {e}")
            # Fallback to sentence transformers
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(Config.DEFAULT_EMBEDDING_MODEL)
            embeddings = model.encode(texts)
            return embeddings.tolist()

class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str = None):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name or Config.DEFAULT_EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

class LLMFactory:
    @staticmethod
    def create_llm(provider: str = None) -> LLMInterface:
        provider = provider or Config.DEFAULT_LLM_PROVIDER
        
        if provider.lower() == 'claude':
            return ClaudeLLM()
        elif provider.lower() == 'gemini':
            return GeminiLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def create_embedding_model(provider: str = None):
        if provider and provider.lower() == 'gemini':
            try:
                return GeminiLLM()  # Will use Gemini embeddings
            except:
                pass
        
        # Default to sentence transformers
        return SentenceTransformerEmbeddings()

class RAGPromptTemplate:
    @staticmethod
    def get_system_prompt() -> str:
        return """You are a helpful assistant that answers questions about the GT New Horizons Minecraft modpack.
        
        Use the provided context documents to answer the user's question. If the information is not available in the context, say so clearly.
        
        When citing information, reference the source documents by their titles. Be accurate and concise in your responses.
        
        If the user asks about specific items, recipes, or game mechanics, provide detailed information from the context."""
    
    @staticmethod
    def format_rag_prompt(question: str, context_chunks: List[Dict], dialogue_history: List[Dict] = None) -> str:
        prompt = "Context documents:\n\n"
        
        for i, chunk in enumerate(context_chunks, 1):
            prompt += f"Document {i} (from {chunk['source_title']}):\n"
            prompt += f"{chunk['text']}\n\n"
        
        if dialogue_history:
            prompt += "Previous conversation:\n"
            for exchange in dialogue_history[-3:]:  # Last 3 exchanges
                prompt += f"User: {exchange['user']}\n"
                prompt += f"Assistant: {exchange['assistant']}\n\n"
        
        prompt += f"Question: {question}\n\n"
        prompt += "Answer based on the context documents above:"
        
        return prompt
    
    @staticmethod
    def get_search_query_prompt(question: str) -> str:
        return f"""Extract the key search terms from this question about GT New Horizons modpack: "{question}"

        Return only the most important keywords that would help find relevant wiki pages.
        Focus on:
        - Item names
        - Machine names  
        - Process names
        - Technology tier names
        - Mod names

        Keywords:"""

if __name__ == "__main__":
    # Test the LLM interfaces
    try:
        llm = LLMFactory.create_llm('gemini')
        response = llm.generate_response("Hello, can you help me with GT New Horizons?")
        print("Gemini response:", response)
        
        embeddings = llm.generate_embeddings(["test text", "another test"])
        print("Embeddings shape:", len(embeddings), len(embeddings[0]) if embeddings else 0)
        
    except Exception as e:
        print(f"Test failed: {e}")