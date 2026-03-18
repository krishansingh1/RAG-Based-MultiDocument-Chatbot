# llm_provider.py
from langchain_google_genai import ChatGoogleGenerativeAI

# You can add more providers here later (OpenAI, Anthropic, etc.)
# without changing any application code.

LLM_REGISTRY = {
    "gemini-pro": {
        "name": "Google Gemini Pro",
        "factory": lambda: ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
        ),
    },
    # ── To add OpenAI later ──
    # "gpt-4": {
    #     "name": "OpenAI GPT-4",
    #     "factory": lambda: ChatOpenAI(
    #         model="gpt-4",
    #         temperature=0.3,
    #     ),
    # },
    #
    # ── To add Anthropic later ──
    # "claude": {
    #     "name": "Anthropic Claude",
    #     "factory": lambda: ChatAnthropic(
    #         model="claude-sonnet-4-20250514",
    #         temperature=0.3,
    #     ),
    # },
}


def get_llm(model_key="gemini-pro"):
    """Return an LLM instance by key. Swap models with a single string change."""
    if model_key not in LLM_REGISTRY:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(LLM_REGISTRY.keys())}")
    return LLM_REGISTRY[model_key]["factory"]()


def list_models():
    """Return available model names for the UI dropdown."""
    return {key: val["name"] for key, val in LLM_REGISTRY.items()}