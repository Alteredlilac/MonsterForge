"""
Configuration for the Gemini LLM client's HTTP retry behavior
(llm/clients/gemini.py).

Plain module-level constants, not a rules/ table: these are runtime
tuning knobs for resilience against transient API errors (rate limits,
server overload), not static game data.
"""

RETRY_ATTEMPTS: int = 5
RETRY_INITIAL_DELAY_SECONDS: float = 1.0
RETRY_MAX_DELAY_SECONDS: float = 20.0
