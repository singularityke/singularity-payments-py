import json

from singularity_payments import STKCallback, STKPushRequest

from .mpesa import mpesa


async def read_json(receive) -> dict:
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break
    return json.loads(body or b"{}")


async def send_json(send, data: dict, status: int = 200) -> None:
    payload = json.dumps(data).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(payload)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    path, method = scope["path"], scope["method"]

    if path == "/api/mpesa/stk-push" and method == "POST":
        payload = await read_json(receive)
        response = await mpesa.stk_push(
            STKPushRequest(
                amount=payload["amount"],
                phone_number=payload["phone_number"],
                account_reference=payload.get("account_reference", "INV-001"),
                transaction_desc=payload.get("transaction_desc", "Payment for order"),
            )
        )
        return await send_json(send, response.model_dump(by_alias=True))

    if path == "/api/mpesa/callback" and method == "POST":
        body = await read_json(receive)
        response = await mpesa.handle_stk_callback(STKCallback.model_validate(body))
        return await send_json(send, response.model_dump(by_alias=True))

    await send_json(send, {"error": "Not found"}, status=404)