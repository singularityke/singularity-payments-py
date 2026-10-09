# AGENTS.md

Guidance for AI agents working on this repository.

## What this project is

`singularity-payments` is a Python SDK for the **Safaricom M-Pesa Daraja API**.
It is a port of the TypeScript project `singularity-payments-js`, specifically the
`packages/core` package.

- **This repo (Python):** `C:\Users\mtume\Desktop\singularity\singularity-payments`
- **Reference repo (TypeScript):** `C:\Users\mtume\Desktop\singularity\singularity-payments-js`

When you need to know how something should behave, read the TypeScript source of
truth in `packages/core/src` and mirror it. The Python code follows the TS
implementation as closely as Python allows.

## Where to get context

Start with the reference mapping below, then read the paired TS file before
changing its Python counterpart.

| TypeScript (`singularity-payments-js/packages/core/src`) | Python (`src/singularity_payments`) |
|---|---|
| `client/mpesa-client.ts` | `client/mpesa_client.py` |
| `types/config.ts` | `types/config.py` |
| `types/mpesa.ts` | `types/mpesa.py` |
| `utils/auth.ts` | `utils/auth.py` |
| `utils/callback.ts` | `utils/callback.py` |
| `utils/errors.ts` | `utils/errors.py` |
| `utils/retry.ts` | `utils/retry.py` |
| `utils/ratelimiter.ts` | `utils/ratelimiter.py` |
| `utils/security.ts` | `utils/security.py` |
| `plugins/stk-push.ts` (empty/no port yet) | (not ported) |
| `__tests__/` | `tests/` |

The TS repo is a monorepo (`core` + framework adapters like express, fastify,
hono, nextjs, nuxt, sveltekit, elysia, react, svelte, vue). The Python repo only
ports `core` so far.

## Project structure

```
src/singularity_payments/
  __init__.py            # Public exports
  client/                # MpesaClient (HTTP calls to Daraja)
  types/                 # Pydantic models
    base.py              # MpesaBaseModel (shared config)
    config.py            # MpesaConfig, MpesaPlugin
    mpesa.py             # All request/response/callback models
  utils/                 # auth, callback, errors, retry, ratelimiter, security
  tests/
    fixtures/            # Reusable test data
    unit/                # Unit tests
```

## Conventions

- **Types are Pydantic v2 models** inheriting `MpesaBaseModel` (`types/base.py`).
- `MpesaBaseModel` sets `populate_by_name=True` and `extra="allow"`, so models
  accept both the snake_case field name and the PascalCase alias.
- **Aliases mirror the raw M-Pesa JSON** exactly, e.g.
  `transaction_id: str = Field(alias="TransactionID")`. Always check the Daraja
  payload key names in the TS types before adding an alias.
- **The client and callbacks are `async`** and built on `httpx`, `tenacity`, and
  Pydantic. Public methods are snake_case; the TS equivalent is camelCase.
- **Docstrings use Google style** (`Args:`, `Returns:`, `Raises:`) and are being
  expanded to be more verbose and developer-friendly.
- Keep the public API names aligned with the TS package where reasonable.

## Tooling

- Package manager / build: **uv** (`pyproject.toml`, `uv.lock`, `uv_build`).
- Python: `.venv` exists (Python 3.12). `requires-python = ">=3.9"`.
- Tests: **pytest** + `pytest-asyncio` (async tests are marked
  `@pytest.mark.asyncio`).
- Run tests with the project venv, e.g.
  `.\.venv\Scripts\python.exe -m pytest`
- Run a quick import/smoke check with
  `.\.venv\Scripts\python.exe -c "import singularity_payments"`.

## Current state / known work in progress

The port is actively being fixed. Expect mismatches with the TS reference.
Known areas to watch (verify against the TS source before changing):

- Field aliases and shared models in `types/mpesa.py` (e.g. B2B callbacks reuse
  a shared `CallbackResult`; verify `Key`/`Value` vs `Name`/`Value`).
- Error classes in `utils/errors.py`: constructor signatures and how subclasses
  call `super().__init__` (the TS version treats `details` as optional).
- `client/mpesa_client.py`: some methods are missing `await` on
  `_make_request`, and the rate-limit/Redis wiring needs alignment with
  `utils/ratelimiter.py`.
- `utils/security.py`: verify the RSA padding (`PKCS1v15`) and file reading.

When fixing something, prefer matching the TypeScript implementation and keep
changes scoped to the file under discussion.
