# Singularity Payments (Python)

A modern, async, type-safe Python SDK for the **Safaricom M-Pesa Daraja API**.
Authentication, retries, rate limiting, typed payloads and callback handling —
without the plumbing.

- **Async-native** — built on `httpx`, designed for FastAPI / ASGI-style apps
- **Type-safe** — Pydantic v2 models for every request, response and callback
- **Resilient** — automatic retries with exponential backoff + jitter
- **Rate-limited out of the box** — in-memory limiter enabled by default, optional Redis for distributed apps
- **Callback router** — parse, validate and answer STK, C2B, B2C, B2B, balance, transaction-status and reversal callbacks
- **Clear errors** — a typed exception hierarchy mapped automatically from Daraja responses
- Works with Python 3.9+

[![PyPI version](https://img.shields.io/pypi/v/singularity-payments.svg)](https://pypi.org/project/singularity-payments/)
[![Python versions](https://img.shields.io/pypi/pyversions/singularity-payments.svg)](https://pypi.org/project/singularity-payments/)

## Supported M-Pesa APIs

Every core Daraja API is one method on `MpesaClient`:

| API | Method |
| --- | --- |
| STK Push (Lipa na M-Pesa Online) | `await mpesa.stk_push(...)` |
| STK Push query | `await mpesa.stk_query(...)` |
| C2B URL registration | `await mpesa.register_c2b_url(...)` |
| C2B simulation (sandbox) | `await mpesa.simulate_c2b(...)` |
| B2C (Business → Customer) | `await mpesa.b2c(...)` |
| B2B (Business → Business) | `await mpesa.b2b(...)` |
| Account balance | `await mpesa.account_balance(...)` |
| Transaction status | `await mpesa.transaction_status(...)` |
| Reversal | `await mpesa.reversal(...)` |
| Dynamic QR generation | `await mpesa.generate_dynamic_qr(...)` |

## Installation

```bash
pip install singularity-payments
```

## Quick start

Set your Daraja credentials as environment variables:

```bash
export MPESA_CONSUMER_KEY=your_consumer_key
export MPESA_CONSUMER_SECRET=your_consumer_secret
export MPESA_PASSKEY=your_passkey
export MPESA_SHORTCODE=174379
export MPESA_ENVIRONMENT=sandbox
```

Create a client:

```python
import os

from singularity_payments import MpesaClient, MpesaConfig

config = MpesaConfig(
    consumer_key=os.environ["MPESA_CONSUMER_KEY"],
    consumer_secret=os.environ["MPESA_CONSUMER_SECRET"],
    passkey=os.environ["MPESA_PASSKEY"],
    short_code=os.environ["MPESA_SHORTCODE"],
    environment=os.environ.get("MPESA_ENVIRONMENT", "sandbox"),
    # Optional extras:
    # callback_url=os.environ["MPESA_CALLBACK_URL"],
    # initiator_name + security_credential are required for B2C/B2B/Reversal/Balance
)

mpesa = MpesaClient(config)
```

Initiate an STK Push:

```python
from singularity_payments import STKPushRequest

response = await mpesa.stk_push(
    STKPushRequest(
        amount=100,
        phone_number="254708374149",
        account_reference="ORDER-123",
        transaction_desc="Payment for order 123",
    )
)
print(response.checkout_request_id)
```

The client is async — call it from FastAPI/ASGI routes, or wrap in
`asyncio.run(...)`. Ready-to-run examples for **FastAPI, Flask, Django and
generic ASGI** live in [`examples/`](examples/).

## Callbacks

Point your Daraja callback URLs at a route and let the client parse, validate
and answer them:

```python
from fastapi import FastAPI, Request
from singularity_payments import STKCallback

app = FastAPI()


@app.post("/mpesa/callback")
async def stk_callback(request: Request):
    body = await request.json()
    response = await mpesa.handle_stk_callback(STKCallback.model_validate(body))
    return response.model_dump(by_alias=True)  # {"ResultCode": 0, "ResultDesc": "Success"}
```

The same pattern covers C2B validation/confirmation, B2C, B2B, account balance,
transaction status and reversal callbacks.

React to results with hooks:

```python
from singularity_payments import CallbackHandlerOptions, MpesaClientOptions

mpesa = MpesaClient(
    config,
    MpesaClientOptions(
        callback_options=CallbackHandlerOptions(
            on_success=lambda data: print(
                f"Paid {data.amount} - receipt {data.mpesa_receipt_number}"
            ),
            on_failure=lambda data: print(data.result_description),
        ),
    ),
)
```

## Error handling

Failures raise typed exceptions, so you can handle each case explicitly:

```python
from singularity_payments import (
    MpesaError,
    MpesaValidationError,
    MpesaRateLimitError,
)

try:
    await mpesa.stk_push(...)
except MpesaValidationError as err:  # e.g. invalid phone number / amount
    ...
except MpesaRateLimitError as err:   # throttled locally or by Daraja
    ...
except MpesaError as err:
    ...
```

The hierarchy mirrors the API: `MpesaError` → `MpesaAuthError`,
`MpesaValidationError`, `MpesaNetworkError`, `MpesaTimeoutError`,
`MpesaRateLimitError`, `MpesaApiError` — with `message`, `code`,
`status_code` and `details` on every error.

## Built-in resilience

- **Auth** — OAuth access tokens are fetched once, cached and refreshed, and
  injected as `Bearer` on every request. STK password + timestamp are generated
  for you.
- **Retries** — exponential backoff with jitter; honors `Retry-After` and only
  retries retryable failures (408/429/5xx). Configure `retry_options` with
  `max_retries`, delays, and an `on_retry` hook.
- **Rate limiting** — on by default (per-key sliding window, ~100 req/min
  configurable). For multi-instance apps use the distributed `RedisRateLimiter`
  with any async Redis-like client.
- **Security** — `encrypt_initiator_password()` produces the RSA PKCS#1 v1.5
  `SecurityCredential` Safaricom expects, and callbacks can be validated
  against the Safaricom IP allowlist with pluggable duplicate detection.

## Documentation

Guides and the full API reference: <https://singularity-payments-docs.vercel.app>

## Support

- Email: mtume.owino@singularity.co.ke
- Issues: https://github.com/singularityke/singularity-payments-py/issues

## Development

```bash
uv sync --dev   # install the project + dev dependencies
uv run pytest   # run the test suite
```

## License

Apache 2.0