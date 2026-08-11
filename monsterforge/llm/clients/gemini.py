"""
Gemini LLM Client

Simple client to interact with Google Gemini models through the
Google Generative AI API.

This module provides a lightweight interface for text generation
used by the application, such as AI-assisted content generation
for game data, descriptions, and transformations.

Requires:
- GEMINI_API_KEY in environment variables

Configuration:
- Model name provided at initialization
- API key loaded from environment variables

Flow:
INIT → GENERATE → (OPTIONAL) SWITCH MODEL

Example:
    client = GeminiClient(llm_model="gemini-1.5-flash")

    description = client.generate_text(
        "Create a fantasy description for an undead creature"
    )

    client.change_llm_model("gemini-1.5-pro")
"""

from dotenv import load_dotenv
import os
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

load_dotenv()

class GeminiClient:
    def __init__(self, llm_model:str):
        self.model_name = llm_model
        self._load_api_key()
        genai.configure(api_key=self._api_key)
        self.model = genai.GenerativeModel(self.model_name)


    def _load_api_key(self)-> None:
        self._api_key = os.getenv("GEMINI_API_KEY")

        if not self._api_key:
                raise ValueError("Missing GEMINI_API_KEY in environment")
        
    def change_llm_model(self, model_name:str)-> None:
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)
      
    def generate_text(self, question: str) -> str:
        try:
            response = self.model.generate_content(question)
            return getattr(response, "text", "")
        except GoogleAPIError as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc
        
    def list_text_models(self) -> list[str]:
        models = genai.list_models()
        return [
            m.name
            for m in models
            if "generateContent" in m.supported_generation_methods
        ]
