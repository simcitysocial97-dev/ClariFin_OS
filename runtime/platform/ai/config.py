"""AI Configuration (Phases 15-20).

Configuration-driven model selection. Change AI models without code changes.

Supported configuration sources (highest precedence first):
  1. Environment variables (AI_*, OPENROUTER_*)
  2. runtime/generated/ai-config.yaml (if present)
  3. Hardcoded defaults

Environment variables:
  AI_PROVIDER        - Provider name: local-small | local-large | openrouter | deterministic
  AI_MODEL           - Model name (e.g., qwen2.5:3b-instruct)
  AI_ENDPOINT        - Ollama endpoint URL
  AI_TEMPERATURE     - Generation temperature (0.0-1.0)
  AI_MAX_TOKENS      - Max output tokens
  OPENROUTER_API_KEY - OpenRouter API key (required for openrouter provider)
  OPENROUTER_MODEL   - OpenRouter model ID (e.g., anthropic/claude-3.5-sonnet)

Example .env:
  AI_PROVIDER=local-small
  AI_MODEL=qwen2.5:3b-instruct
  AI_ENDPOINT=http://localhost:11434
  AI_TEMPERATURE=0.1
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": "local-small",
    "model": "qwen2.5:3b-instruct",
    "endpoint": "http://localhost:11434",
    "temperature": 0.1,
    "max_tokens": 4096,
    "privacy": "local",
    "latency_budget_ms": 30_000,
    "cost_budget_usd": 0.0,
    "fallback_chain": [
        "local-small",
        "local-large",
        "openrouter",
        "deterministic-fallback",
    ],
    "providers": {
        "local-small": {
            "kind": "local",
            "default_model": "qwen2.5:3b-instruct",
            "endpoint": "http://localhost:11434",
            "enabled": True,
        },
        "local-large": {
            "kind": "local",
            "default_model": "qwen2.5-coder:14b",
            "endpoint": "http://localhost:11434",
            "enabled": False,  # opt-in only
        },
        "openrouter": {
            "kind": "external",
            "default_model": "anthropic/claude-3.5-sonnet",
            "endpoint": "https://openrouter.ai/api/v1",
            "api_key_env": "OPENROUTER_API_KEY",
            "enabled": False,  # disabled by default per design
        },
        "deterministic-fallback": {
            "kind": "local",
            "default_model": "deterministic",
            "enabled": True,
        },
    },
}


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def _load_from_env() -> dict[str, Any]:
    """Load configuration from environment variables."""
    config: dict[str, Any] = {}
    for key, value in os.environ.items():
        if key.startswith("AI_"):
            config_key = key[len("AI_") :].lower()
            config[config_key] = value
        elif key.startswith("OPENROUTER_"):
            config_key = "openrouter_" + key[len("OPENROUTER_") :].lower()
            config[config_key] = value
    return config


def _load_from_yaml(path: Path) -> dict[str, Any] | None:
    """Load configuration from YAML file. Returns None if not found."""
    if not path.exists():
        return None
    try:
        import yaml

        data = yaml.safe_load(path.read_text())
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def load_config() -> dict[str, Any]:
    """Load AI configuration from all sources, merged with precedence."""
    config = dict(DEFAULT_CONFIG)

    # Layer 1: YAML config file (lowest precedence among overrides)
    yaml_path = Path("runtime/generated/ai-config.yaml")
    yaml_cfg = _load_from_yaml(yaml_path)
    if yaml_cfg:
        config.update(yaml_cfg)
        # Merge provider configs
        if "providers" in yaml_cfg:
            for pname, pconf in yaml_cfg["providers"].items():
                if pname in config.get("providers", {}):
                    config["providers"][pname].update(pconf)
                else:
                    config.setdefault("providers", {})[pname] = pconf

    # Layer 2: Environment variables (highest precedence)
    env_cfg = _load_from_env()
    config.update(env_cfg)
    # Ensure providers are updated from env
    if env_cfg.get("providers"):
        for pname, pconf in env_cfg["providers"].items():
            if pname in config.get("providers", {}):
                config["providers"][pname].update(pconf)
            else:
                config.setdefault("providers", {})[pname] = pconf

    return config


@dataclass(frozen=True)
class AIConfig:
    """Immutable snapshot of resolved AI configuration."""

    provider: str = "local-small"
    model: str = "qwen2.5:3b-instruct"
    endpoint: str = "http://localhost:11434"
    temperature: float = 0.1
    max_tokens: int = 4096
    privacy: str = "local"
    latency_budget_ms: int = 30_000
    cost_budget_usd: float = 0.0
    fallback_chain: list[str] = field(
        default_factory=lambda: [
            "local-small",
            "local-large",
            "openrouter",
            "deterministic-fallback",
        ]
    )
    providers: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AIConfig:
        fallback = data.get(
            "fallback_chain",
            ["local-small", "local-large", "openrouter", "deterministic-fallback"],
        )
        providers = data.get("providers", {})
        return cls(
            provider=data.get("provider", "local-small"),
            model=data.get("model", "qwen2.5:3b-instruct"),
            endpoint=data.get("endpoint", "http://localhost:11434"),
            temperature=float(data.get("temperature", 0.1)),
            max_tokens=int(data.get("max_tokens", 4096)),
            privacy=data.get("privacy", "local"),
            latency_budget_ms=int(data.get("latency_budget_ms", 30_000)),
            cost_budget_usd=float(data.get("cost_budget_usd", 0.0)),
            fallback_chain=fallback,
            providers=providers,
        )

    def with_provider(self, provider_name: str) -> AIConfig:
        """Create a new config with a different primary provider."""
        new_providers = dict(self.providers)
        if provider_name in new_providers:
            new_providers[provider_name]["enabled"] = True
            # Move to front of fallback chain
            chain = [provider_name] + [
                p for p in self.fallback_chain if p != provider_name
            ]
        else:
            chain = list(self.fallback_chain)
        return AIConfig(
            provider=provider_name,
            model=new_providers.get(provider_name, {}).get("default_model", self.model),
            endpoint=new_providers.get(provider_name, {}).get(
                "endpoint", self.endpoint
            ),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            privacy=self.privacy,
            latency_budget_ms=self.latency_budget_ms,
            cost_budget_usd=self.cost_budget_usd,
            fallback_chain=chain,
            providers=new_providers,
        )

    def get_provider_config(self, name: str) -> dict[str, Any] | None:
        return self.providers.get(name)

    def is_provider_enabled(self, name: str) -> bool:
        pc = self.providers.get(name, {})
        return bool(pc.get("enabled", False))

    def is_external_provider(self, name: str) -> bool:
        pc = self.providers.get(name, {})
        return pc.get("kind") == "external"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_loaded_config: dict[str, Any] | None = None


def get_ai_config() -> AIConfig:
    """Get the current AI configuration (loads once, cached)."""
    global _loaded_config
    if _loaded_config is None:
        _loaded_config = load_config()
    return AIConfig.from_dict(_loaded_config)


def reload_ai_config() -> AIConfig:
    """Force-reload configuration (useful in tests)."""
    global _loaded_config
    _loaded_config = load_config()
    return AIConfig.from_dict(_loaded_config)


def set_ai_config(**overrides: Any) -> AIConfig:
    """Override specific config values (for testing)."""
    global _loaded_config
    if _loaded_config is None:
        _loaded_config = dict(DEFAULT_CONFIG)
    _loaded_config.update(overrides)
    return AIConfig.from_dict(_loaded_config)
