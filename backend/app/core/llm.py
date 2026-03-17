from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_llm(temperature: float = 0.7, max_tokens: int = 1000):
    """
    Returns a LangChain chat model based on LLM_PROVIDER env var.
    Swap providers by changing LLM_PROVIDER in .env — no code changes needed.
    """
    if settings.LLM_PROVIDER == "openai":
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.OPENAI_API_KEY,
        )
    # Default: anthropic
    return ChatAnthropic(
        model=settings.ANTHROPIC_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.ANTHROPIC_API_KEY,
    )
