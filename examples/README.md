# Singularity Payments — Framework Examples

Minimal servers that show how to integrate the Python SDK with each web
framework. These mirror the integration guides in the documentation
(`content/docs/integrations/` in the docs repo):

| Directory  | Framework / style        | Server command                              |
| ---------- | ------------------------ | ------------------------------------------- |
| `fastapi/` | FastAPI (async)          | `uvicorn app.main:app --reload`             |
| `flask/`   | Flask (WSGI, sync)       | `flask --app app:create_app run`            |
| `asgi/`    | Generic ASGI callable    | `uvicorn app.asgi:app --reload`             |
| `django/`  | Django (sync views)      | `python manage.py runserver`                |

Each example exposes at least:

- `POST /api/mpesa/stk-push` — initiate an STK Push (needs real M-Pesa
  credentials and a public callback URL).
- `POST /api/mpesa/callback` — receive the STK Push callback and parse it with
  the SDK's callback handler (works without real credentials).

## Setup

The examples import the SDK from the repository root, so install it (editable)
together with the framework you want:

```bash
# from the repository root
uv pip install -e . fastapi "uvicorn[standard]" flask django python-dotenv
```

Each example also ships a `requirements.txt` listing what its server needs.
Copy `.env.example` to `.env` and fill in your M-Pesa credentials (sandbox
credentials are enough for the STK push route).

## Verify the SDK works on each framework

```bash
python verify.py
```

This boots all four servers on random local ports, POSTs a realistic STK Push
callback to each `/api/mpesa/callback` route and asserts the SDK returns a
`ResultCode` of `0`. It does **not** call the Daraja API, so no credentials are
required.