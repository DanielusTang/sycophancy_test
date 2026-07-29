#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared LLM plumbing for the false-presupposition sycophancy stress test.

Not itself an "agent" — this holds the pieces every agent (HumanProxy, Target,
Judge) needs: DeepSeek client construction, the retrying `BaseLLM` wrapper around
the openai SDK, logging, and small generic helpers. It has no dependency on the
agent modules (`false_presuppositions_proxy.py` / `_target.py` / `_judge.py`), which
avoids a circular import with `false_presuppositions_main.py` (the CLI/orchestrator,
which imports from all of these).
"""

from __future__ import annotations

import logging
import os
from typing import Optional

# Load DEEPSEEK_API_KEY (and any other vars) from the repo-root .env if present.
# Every other module in this package imports something from here, so this runs once
# at first import regardless of which entry point (main / naturalistic / adversarial)
# is launched.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
except ImportError:
    pass

import openai
from openai import OpenAI
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sycophancy")

_run_log_handler: Optional[logging.FileHandler] = None


def attach_run_log_file(path: str) -> None:
    """Tee this logger's output (cache stats, retries, turn banners) to a per-run file.

    Console-only logging loses the per-call cache read/write lines whenever a run isn't
    launched under nohup with redirection; the .log file next to the JSONL keeps them.
    Replaces the previous run's handler so batch loops in one process don't double-log."""
    global _run_log_handler
    if _run_log_handler is not None:
        logger.removeHandler(_run_log_handler)
        _run_log_handler.close()
    _run_log_handler = logging.FileHandler(path, encoding="utf-8")
    _run_log_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_run_log_handler)

# --------------------------------------------------------------------------- #
# API configuration constants
# --------------------------------------------------------------------------- #
# Base URL is env-overridable so the same code runs against the hosted DeepSeek API
# OR a local cluster serving R1/V3 behind an OpenAI-compatible endpoint (vLLM, SGLang,
# TGI, Ollama, ...). For a local server, set e.g.
#   export DEEPSEEK_BASE_URL=http://<node>:8000/v1
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
# Model IDs are also env-overridable (and still override-able per run via the CLI flags).
# On a local cluster this is usually the full HF repo id, e.g.
#   export DEEPSEEK_CHAT_MODEL=deepseek-ai/DeepSeek-V3
DEFAULT_MODEL = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-v4-pro")  # Proxy (DeepSeek V4 Pro)
REQUEST_TIMEOUT = 300.0  # per-request timeout (seconds); reasoning models are slower

# tenacity retry: exponential backoff only for "retryable" network / rate-limit
# errors. The openai SDK's own max_retries is disabled (set to 0); retries are
# controlled centrally by tenacity.
RETRYABLE_ERRORS = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.InternalServerError,
    # Mid-stream resets (long thinking-mode streams) often surface as a RAW socket/httpx error
    # that the openai SDK does NOT wrap as APIConnectionError — e.g. "[Errno 54] Connection reset
    # by peer". Retry those too. ConnectionError is the builtin parent of ConnectionResetError /
    # BrokenPipeError; httpx.TransportError covers RemoteProtocolError / ReadError / ConnectError.
    ConnectionError,
)
try:
    import httpx as _httpx
    RETRYABLE_ERRORS = RETRYABLE_ERRORS + (_httpx.TransportError,)
except ImportError:
    pass

api_retry = retry(
    reraise=True,
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(RETRYABLE_ERRORS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


def is_deepseek_reasoner(model: str) -> bool:
    """Whether `model` is a DeepSeek reasoning model (R1), which drops sampling params.

    Matches both the hosted API id ("deepseek-reasoner") and the model ids a local
    cluster typically serves R1 under (e.g. "deepseek-ai/DeepSeek-R1", "DeepSeek-R1").
    Override with the DEEPSEEK_REASONER_HINT env var if your server uses another name.

    Module-level so callers that only have a model STRING (e.g. the CLI validating
    --target-temperature before any agent exists) share one marker list with the
    BaseLLM.is_reasoner property.
    """
    name = model.lower()
    hint = os.getenv("DEEPSEEK_REASONER_HINT", "").lower()
    markers = ["reasoner", "-r1", "/r1", "deepseek-r1", "r1-"]
    if hint:
        markers.append(hint)
    return any(m in name for m in markers)


# --------------------------------------------------------------------------- #
# BaseLLM: base class for all agents
# --------------------------------------------------------------------------- #
class BaseLLM:
    """Wraps the common logic of calling DeepSeek via the openai SDK (with tenacity retries)."""

    def __init__(
        self,
        client: OpenAI,
        model: str = DEFAULT_MODEL,
        *,
        name: str = "BaseLLM",
        default_temperature: float = 0.7,
        max_tokens: int = 2048,
        extra_body: Optional[dict] = None,
        stream: bool = False,
    ) -> None:
        self.client = client
        self.model = model
        self.name = name
        self.default_temperature = default_temperature
        self.max_tokens = max_tokens
        # Provider-specific params the OpenAI SDK has no field for (e.g. Qwen's
        # enable_thinking). Forwarded verbatim on every call when set.
        self.extra_body = extra_body
        # The 智增增 Qwen endpoint rejects enable_thinking=True on non-stream calls
        # ("only support stream call"), so thinking-mode agents must stream and
        # accumulate the deltas. Chat mode stays a single non-stream call.
        self.stream = stream

    @property
    def is_reasoner(self) -> bool:
        """Whether this agent's model is a DeepSeek reasoning model (R1)."""
        return is_deepseek_reasoner(self.model)

    @api_retry
    def _chat(
        self,
        messages: list[dict],
        *,
        temperature: Optional[float] = None,
        response_format: Optional[dict] = None,
        return_reasoning: bool = False,
    ):
        """
        Make a single chat completion call to DeepSeek.

        Returns the text content by default. If return_reasoning=True, returns a
        (content, reasoning_content) tuple — reasoning_content is the model's
        chain-of-thought (only populated by reasoning models like deepseek-reasoner;
        empty string otherwise).
        """
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "timeout": REQUEST_TIMEOUT,
        }
        # deepseek-reasoner does not support temperature / top_p / penalties — omit them.
        if not self.is_reasoner:
            kwargs["temperature"] = self.default_temperature if temperature is None else temperature
        # response_format (json_object) is unsupported by deepseek-reasoner AND by the Qwen
        # 智增增 endpoint (which uses extra_body/streaming for thinking). In those cases we skip
        # it and rely on the callers' regex JSON extraction.
        if (response_format is not None and not self.is_reasoner
                and not self.stream and not self.extra_body):
            kwargs["response_format"] = response_format
        if self.extra_body:
            kwargs["extra_body"] = self.extra_body

        if self.stream:
            content, reasoning = self._chat_streamed(kwargs)
        else:
            response = self.client.chat.completions.create(**kwargs)
            self._log_cache_usage(getattr(response, "usage", None))
            message = response.choices[0].message
            content = (message.content or "").strip()
            # DeepSeek/Qwen expose the chain-of-thought as reasoning_content;
            # OpenRouter normalizes it to `reasoning`. Accept either.
            reasoning = (getattr(message, "reasoning_content", None)
                         or getattr(message, "reasoning", None) or "").strip()
        if return_reasoning:
            return content, reasoning
        return content

    def _log_cache_usage(self, usage) -> None:
        """Log the server-side prefix-cache stats for this call.

        DeepSeek caches automatically and reports prompt_cache_hit_tokens /
        prompt_cache_miss_tokens; other OpenAI-compatible providers report
        prompt_tokens_details.cached_tokens instead. hit=0 across a whole multi-turn
        run means the prompt prefix is not byte-stable and caching never engaged."""
        if usage is None:
            return
        hit = getattr(usage, "prompt_cache_hit_tokens", None)
        if hit is not None:
            miss = getattr(usage, "prompt_cache_miss_tokens", 0) or 0
            logger.info("%s (%s) cache: hit=%d miss=%d", self.name, self.model,
                        hit or 0, miss)
            return
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        details = getattr(usage, "prompt_tokens_details", None)
        cached = getattr(details, "cached_tokens", 0) or 0
        logger.info("%s (%s) cache: hit=%d miss=%d", self.name, self.model,
                    cached, prompt - cached)

    def _chat_streamed(self, kwargs: dict) -> tuple[str, str]:
        """Stream a completion and accumulate (content, reasoning_content).

        Required for Qwen's thinking mode on the 智增增 endpoint. The chain-of-thought
        arrives in the delta's `reasoning_content` field, separate from `content`.
        """
        kwargs = {**kwargs, "stream": True}
        content, reasoning = [], []
        usage = None
        for chunk in self.client.chat.completions.create(**kwargs):
            # Usage arrives (if at all) on a final chunk with empty choices.
            usage = getattr(chunk, "usage", None) or usage
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            reasoning.append(getattr(delta, "reasoning_content", None)
                             or getattr(delta, "reasoning", None) or "")
            content.append(getattr(delta, "content", None) or "")
        self._log_cache_usage(usage)
        return "".join(content).strip(), "".join(reasoning).strip()


# --------------------------------------------------------------------------- #
# Client construction / small generic helpers
# --------------------------------------------------------------------------- #
def build_client(api_key: str, base_url: str = DEEPSEEK_BASE_URL) -> OpenAI:
    # max_retries=0: disable the SDK's built-in retries, let tenacity control them centrally.
    # base_url is overridable so the Target-under-test can point at a self-hosted vLLM/SGLang
    # endpoint on the cluster (e.g. http://localhost:8000/v1) while the Proxy/Judge keep
    # hitting the hosted DeepSeek API.
    return OpenAI(api_key=api_key, base_url=base_url, max_retries=0)


def _preview(text: str, limit: Optional[int] = None) -> str:
    text = " ".join((text or "").split())
    if limit is None or len(text) <= limit:
        return text
    return text[:limit] + " …"
