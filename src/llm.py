"""
LLM Client Interface Module for Global News AI - Phase 5

Provides a unified client wrapper supporting Google Gemini API (google-genai / google-generativeai)
and OpenAI API for generating grounded, hallucination-free answers based on retrieved news context.
"""

from typing import Optional
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load .env variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_llm_config():
    """
    Retrieves LLM configuration parameters from environment variables.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    model_name = os.getenv("LLM_MODEL", "gemini-3.6-flash").strip()

    return {
        "provider": provider,
        "gemini_api_key": gemini_key,
        "openai_api_key": openai_key,
        "model": model_name,
    }


def generate_answer_with_gemini(
    prompt: str,
    system_instruction: str,
    api_key: str,
    model_name: str = "gemini-3.6-flash",



    temperature: float = 0.2,
) -> str:
    """
    Generates a response using Google Gemini API.
    Supports both modern google-genai SDK and fallback google-generativeai SDK.
    """
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("Gemini API key is not configured in .env file.")

    # Try modern google-genai SDK first
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        if response and response.text:
            return response.text.strip()
        else:
            raise ValueError("Gemini API returned an empty text response.")

    except ImportError:
        # Fallback to google-generativeai legacy SDK
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
            )
            response = model.generate_content(
                prompt,
                generation_config={"temperature": temperature},
            )
            if response and response.text:
                return response.text.strip()
            else:
                raise ValueError("Gemini API returned an empty text response.")
        except Exception as err:
            logger.error(f"Gemini LLM Generation Error: {err}")
            raise


def generate_answer_with_openai(
    prompt: str,
    system_instruction: str,
    api_key: str,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.2,
) -> str:
    """
    Generates a response using OpenAI API.
    """
    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError("OpenAI API key is not configured in .env file.")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        else:
            raise ValueError("OpenAI API returned an empty response.")
    except Exception as err:
        logger.error(f"OpenAI LLM Generation Error: {err}")
        raise


def generate_grounded_answer(
    prompt: str,
    system_instruction: str,
    temperature: float = 0.2,
) -> str:
    """
    Master function to dispatch prompt and system instructions to configured LLM provider.
    """
    config = get_llm_config()
    provider = config["provider"]

    if provider == "gemini":
        return generate_answer_with_gemini(
            prompt=prompt,
            system_instruction=system_instruction,
            api_key=config["gemini_api_key"],
            model_name=config["model"],
            temperature=temperature,
        )
    elif provider == "openai":
        return generate_answer_with_openai(
            prompt=prompt,
            system_instruction=system_instruction,
            api_key=config["openai_api_key"],
            model_name=config["model"],
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unsupported LLM provider '{provider}'. Choose 'gemini' or 'openai'.")
