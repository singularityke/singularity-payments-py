import asyncio
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from singularity_payments import STKCallback, STKPushRequest

from .mpesa import mpesa


@csrf_exempt
@require_POST
def stk_push(request):
    """Initiate an STK Push. Needs real M-Pesa credentials + a public URL."""
    payload = json.loads(request.body)
    response = asyncio.run(
        mpesa.stk_push(
            STKPushRequest(
                amount=payload["amount"],
                phone_number=payload["phone_number"],
                account_reference=payload.get("account_reference", "INV-001"),
                transaction_desc=payload.get("transaction_desc", "Payment for order"),
            )
        )
    )
    return JsonResponse(response.model_dump(by_alias=True))


@csrf_exempt
@require_POST
def stk_callback(request):
    """Receive the M-Pesa STK Push callback and parse it with the SDK."""
    callback = STKCallback.model_validate(json.loads(request.body))
    response = asyncio.run(mpesa.handle_stk_callback(callback))
    return JsonResponse(response.model_dump(by_alias=True))