"""Vertex AI Gemini wrapper."""

from __future__ import annotations

import json
import re
from typing import Any

import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel

from pipeline.config import gcp_project_id, load_config, llm_model

_initialized = False
_model: GenerativeModel | None = None


def _ensure_init() -> GenerativeModel:
    global _initialized, _model
    if _model is None:
        cfg = load_config()
        vertexai.init(
            project=gcp_project_id(),
            location=cfg["gcp"]["location"],
        )
        _model = GenerativeModel(llm_model())
        _initialized = True
    return _model


def generate_text(
    system: str,
    user: str,
    *,
    json_mode: bool = False,
    temperature: float = 0.1,
) -> str:
    model = _ensure_init()
    prompt = f"{system}\n\n---\n\n{user}"
    gen_cfg = GenerationConfig(
        temperature=temperature,
        max_output_tokens=8192,
    )
    if json_mode:
        gen_cfg = GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )
    response = model.generate_content(prompt, generation_config=gen_cfg)
    return response.text or ""


def parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)
