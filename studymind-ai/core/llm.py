# core/llm.py
"""
LLM wrapper — FIXED version.

Changes:
1. Graceful fallback: if OpenAI key is missing/invalid, automatically
   tries Ollama locally; if Ollama is also unavailable, returns a clear
   error message instead of crashing.
2. simple_chat() returns a string in ALL cases — never raises to the UI.
3. stream_chat() catches errors and yields an error message token.
"""

import os
from typing import Generator
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL      = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
TEMPERATURE    = float(os.getenv("LLM_TEMPERATURE", "0.3"))
MAX_TOKENS     = int(os.getenv("LLM_MAX_TOKENS", "2048"))

_USE_OPENAI = (
    bool(OPENAI_API_KEY)
    and not OPENAI_API_KEY.startswith("sk-your")
    and LLM_MODEL not in ("llama3", "llama2", "mistral", "phi3", "gemma")
    and not LLM_MODEL.startswith("ollama:")
)

_USE_OLLAMA = (
    LLM_MODEL in ("llama3", "llama2", "mistral", "phi3", "gemma")
    or LLM_MODEL.startswith("ollama:")
)

# Singleton
_llm_instance = None


def get_llm(temperature: float = TEMPERATURE):
    """Return the configured LLM singleton."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    if _USE_OLLAMA:
        try:
            from langchain_community.llms import Ollama
            model_name = LLM_MODEL.replace("ollama:", "")
            _llm_instance = Ollama(model=model_name, temperature=temperature)
            print(f"[llm] Using Ollama: {model_name}")
        except Exception as e:
            print(f"[llm] Ollama unavailable: {e}")
            _llm_instance = None
    elif _USE_OPENAI:
        try:
            from langchain_openai import ChatOpenAI
            _llm_instance = ChatOpenAI(
                model=LLM_MODEL,
                openai_api_key=OPENAI_API_KEY,
                temperature=temperature,
                max_tokens=MAX_TOKENS,
            )
            print(f"[llm] Using OpenAI: {LLM_MODEL}")
        except Exception as e:
            print(f"[llm] OpenAI unavailable: {e}")
            _llm_instance = None
    else:
        print("[llm] No valid LLM configured. Set OPENAI_API_KEY in .env")

    return _llm_instance


def get_creative_llm():
    return get_llm(temperature=0.7)


def get_precise_llm():
    return get_llm(temperature=0.1)


def simple_chat(prompt: str, system: str = "", temperature: float = TEMPERATURE) -> str:
    """
    Single-turn completion. Always returns a string — never raises.
    """
    llm = get_llm(temperature)
    if llm is None:
        return (
            "⚠️ No LLM configured. Please add your `OPENAI_API_KEY` to the `.env` file "
            "and restart the app, or install Ollama and set `LLM_MODEL=llama3`."
        )

    try:
        if _USE_OLLAMA:
            full = f"{system}\n\n{prompt}" if system else prompt
            resp = llm.invoke(full)
            return resp if isinstance(resp, str) else str(resp)
        else:
            from langchain_core.documents import HumanMessage, SystemMessage
            msgs = []
            if system:
                msgs.append(SystemMessage(content=system))
            msgs.append(HumanMessage(content=prompt))
            resp = llm.invoke(msgs)
            return resp.content

    except Exception as e:
        err = str(e)
        if "api_key" in err.lower() or "authentication" in err.lower():
            return "⚠️ Invalid OpenAI API key. Please check your `.env` file."
        if "rate_limit" in err.lower():
            return "⚠️ OpenAI rate limit hit. Please wait a moment and try again."
        if "insufficient_quota" in err.lower():
            return "⚠️ OpenAI quota exceeded. Check your billing at platform.openai.com."
        return f"⚠️ LLM error: {err}"


def stream_chat(prompt: str, system: str = "", temperature: float = TEMPERATURE) -> Generator:
    """Streaming generator — yields text tokens."""
    llm = get_llm(temperature)
    if llm is None:
        yield "⚠️ No LLM configured. Add OPENAI_API_KEY to .env and restart."
        return
    try:
        if _USE_OLLAMA:
            full = f"{system}\n\n{prompt}" if system else prompt
            for chunk in llm.stream(full):
                yield chunk
        else:
            from langchain_core.documents import HumanMessage, SystemMessage
            msgs = []
            if system:
                msgs.append(SystemMessage(content=system))
            msgs.append(HumanMessage(content=prompt))
            for chunk in llm.stream(msgs):
                yield chunk.content
    except Exception as e:
        yield f"\n⚠️ Stream error: {e}"


def count_tokens(text: str) -> int:
    return len(text) // 4