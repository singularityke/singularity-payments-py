#!/usr/bin/env python3
"""Boot every example server and confirm the SDK's callback handling works.

Starts the FastAPI, Flask, plain-ASGI and Django example servers on random
local ports, POSTs a realistic STK Push callback to each
``/api/mpesa/callback`` route and asserts the SDK returns a ``ResultCode`` of
``0``. Requires the SDK and the framework packages to be installed in the
active environment:

    uv pip install -e . fastapi "uvicorn[standard]" flask django python-dotenv

Run from the ``examples/`` directory::

    python verify.py

"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

CALLBACK_PAYLOAD = {
    "Body": {
        "stkCallback": {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": "ws_CO_191220191020363925",
            "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    {"Name": "Amount", "Value": 1.0},
                    {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                    {"Name": "TransactionDate", "Value": 20240101120000},
                    {"Name": "PhoneNumber", "Value": 254712345678},
                ]
            },
        }
    }
}

SERVERS = [
    {
        "name": "fastapi",
        "cwd": ROOT / "fastapi",
        "cmd": lambda port: [
            PYTHON, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(port),
        ],
    },
    {
        "name": "asgi",
        "cwd": ROOT / "asgi",
        "cmd": lambda port: [
            PYTHON, "-m", "uvicorn", "app.asgi:app",
            "--host", "127.0.0.1", "--port", str(port),
        ],
    },
    {
        "name": "flask",
        "cwd": ROOT / "flask",
        "cmd": lambda port: [
            PYTHON, "-m", "flask", "--app", "app:create_app", "run",
            "--host", "127.0.0.1", "--port", str(port),
        ],
    },
    {
        "name": "django",
        "cwd": ROOT / "django",
        "cmd": lambda port: [
            PYTHON, "manage.py", "runserver",
            f"127.0.0.1:{port}", "--noreload",
        ],
    },
]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def base_env(port: int) -> dict:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("MPESA_")
        and k not in ("FLASK_APP", "FLASK_ENV", "DJANGO_SETTINGS_MODULE")
    }
    # Placeholder credentials: enough for instantiation and callback parsing.
    # The verify flow never calls the Daraja API.
    env.update(
        {
            "MPESA_CONSUMER_KEY": "test_consumer_key",
            "MPESA_CONSUMER_SECRET": "test_consumer_secret",
            "MPESA_PASSKEY": "test_passkey",
            "MPESA_SHORTCODE": "174379",
            "MPESA_ENVIRONMENT": "sandbox",
            "MPESA_CALLBACK_URL": f"http://127.0.0.1:{port}/api/mpesa/callback",
            "MPESA_INITIATOR_NAME": "testapi",
            "MPESA_SECURITY_CREDENTIAL": "test_security_credential",
            "MPESA_RESULT_URL": f"http://127.0.0.1:{port}/api/mpesa/result",
            "MPESA_TIMEOUT_URL": f"http://127.0.0.1:{port}/api/mpesa/timeout",
            "PYTHONUNBUFFERED": "1",
        }
    )
    return env


def http_request(url, method="GET", body=None, timeout=5):
    """Return (status, json) or (None, None) when the server is unreachable."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read() or b"{}"
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read() or b"{}"
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw.decode(errors="replace")}
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        return None, None


def wait_until_ready(url, timeout=45):
    """Any HTTP response (even 404/405) means the server is listening."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, _ = http_request(url)
        if status is not None:
            return True
        time.sleep(0.4)
    return False


def run_framework(server):
    name, cwd = server["name"], server["cwd"]
    port = free_port()
    url = f"http://127.0.0.1:{port}/api/mpesa/callback"
    log_path = Path(tempfile.gettempdir()) / f"singularity-example-{name}.log"
    log = open(log_path, "w+b")

    proc = subprocess.Popen(
        server["cmd"](port),
        cwd=str(cwd),
        env=base_env(port),
        stdout=log,
        stderr=subprocess.STDOUT,
    )

    try:
        def tail():
            log.flush()
            log.seek(0)
            return log.read().decode(errors="replace")[-4000:]

        if not wait_until_ready(url):
            proc.kill()
            proc.wait()
            return name, False, (
                f"server did not become ready on port {port}\n"
                f"--- {log_path} ---\n{tail()}"
            )

        # The actual check: parse a real M-Pesa STK callback through the SDK.
        status, body = http_request(url, method="POST", body=CALLBACK_PAYLOAD)
        if status != 200:
            return name, False, (
                f"callback returned HTTP {status} (expected 200)\n"
                f"body: {body}\n"
                f"--- {log_path} ---\n{tail()}"
            )
        result_code = body.get("ResultCode")
        if result_code != 0:
            return name, False, (
                f"callback returned ResultCode={result_code!r} (expected 0)\n"
                f"body: {body}\n"
                f"--- {log_path} ---\n{tail()}"
            )
        return name, True, f"POST /api/mpesa/callback -> 200 {body}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        log.close()


def main() -> int:
    failures = 0
    print(f"Python: {PYTHON}")
    for server in SERVERS:
        name, ok, detail = run_framework(server)
        marker = "PASS" if ok else "FAIL"
        print(f"[{marker}] {name}: {detail}")
        if not ok:
            failures += 1

    print(f"\n{len(SERVERS) - failures}/{len(SERVERS)} frameworks passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())