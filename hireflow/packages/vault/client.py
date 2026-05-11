"""
Secrets vault abstraction.

MVP backend: environment variables (VAULT_BACKEND=env).
GA backend: HashiCorp Vault (VAULT_BACKEND=hashicorp) or
            AWS Secrets Manager (VAULT_BACKEND=aws_secrets_manager).

All callers use get_secret(key) / put_secret(key, value) — never read env
variables for credentials directly. This lets us swap backends without
touching agent code.
"""

import json
import os
from abc import ABC, abstractmethod


class VaultBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None: ...

    @abstractmethod
    def put(self, key: str, value: str) -> None: ...


class EnvVaultBackend(VaultBackend):
    """Reads secrets from environment variables. MVP only."""

    def get(self, key: str) -> str | None:
        env_key = key.upper().replace("/", "_").replace("-", "_")
        return os.environ.get(env_key)

    def put(self, key: str, value: str) -> None:
        env_key = key.upper().replace("/", "_").replace("-", "_")
        os.environ[env_key] = value


class HashiCorpVaultBackend(VaultBackend):
    """HashiCorp Vault via hvac. Configured for GA."""

    def __init__(self) -> None:
        import hvac  # type: ignore[import]

        self._client = hvac.Client(
            url=os.environ["VAULT_ADDR"],
            token=os.environ["VAULT_TOKEN"],
        )
        if not self._client.is_authenticated():
            raise RuntimeError("HashiCorp Vault authentication failed")

    def get(self, key: str) -> str | None:
        path, field = key.rsplit("/", 1) if "/" in key else ("hireflow", key)
        try:
            secret = self._client.secrets.kv.v2.read_secret_version(path=path)
            return secret["data"]["data"].get(field)
        except Exception:
            return None

    def put(self, key: str, value: str) -> None:
        path, field = key.rsplit("/", 1) if "/" in key else ("hireflow", key)
        self._client.secrets.kv.v2.create_or_update_secret(
            path=path, secret={field: value}
        )


def _build_backend() -> VaultBackend:
    backend = os.environ.get("VAULT_BACKEND", "env").lower()
    if backend == "env":
        return EnvVaultBackend()
    if backend == "hashicorp":
        return HashiCorpVaultBackend()
    raise ValueError(f"Unknown VAULT_BACKEND: {backend!r}")


_backend: VaultBackend | None = None


def _get_backend() -> VaultBackend:
    global _backend
    if _backend is None:
        _backend = _build_backend()
    return _backend


def get_secret(key: str) -> str:
    value = _get_backend().get(key)
    if value is None:
        raise KeyError(f"Secret not found in vault: {key!r}")
    return value


def get_secret_json(key: str) -> dict:
    return json.loads(get_secret(key))


def put_secret(key: str, value: str) -> None:
    _get_backend().put(key, value)


def get_linkedin_credentials(persona_vault_key: str) -> dict:
    """Returns {"username": ..., "password": ..., "proxy_url": ...}"""
    return get_secret_json(persona_vault_key)
