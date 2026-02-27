"""LLM utilities using OpenAI API."""
from openai import OpenAI
from typing import Optional
import os


def get_llm_client(api_key: Optional[str] = None) -> OpenAI:
    """Get OpenAI client. Uses provided key or falls back to env var."""
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("No OpenAI API key available (neither user key nor OPENAI_API_KEY env var)")
    return OpenAI(api_key=key)


def generate_text(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Generate text using OpenAI API.
    
    Args:
        system_prompt: System instructions
        user_prompt: User query
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        api_key: Optional user-provided API key (BYO LLM)
        
    Returns:
        Generated text content
    """
    client = get_llm_client(api_key=api_key)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return response.choices[0].message.content or ""
