import asyncio

from flask import Blueprint, jsonify, request

from singularity_payments import (
    C2BCallback,
    MpesaApiError,
    STKCallback,
    STKPushRequest,
)

from .mpesa import mpesa

bp = Blueprint("mpesa", __name__, url_prefix="/api/mpesa")


@bp.post("/stk-push")
def stk_push():
    payload = request.get_json(force=True)
    try:
        response = asyncio.run(
            mpesa.stk_push(
                STKPushRequest(
                    amount=payload["amount"],
                    phone_number=payload["phone_number"],
                    account_reference=payload.get("account_reference", "INV-001"),
                    transaction_desc=payload.get(
                        "transaction_desc", "Payment for order"
                    ),
                )
            )
        )
    except MpesaApiError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(response.model_dump(by_alias=True))


@bp.post("/callback")
def stk_callback():
    callback = STKCallback.model_validate(request.get_json(force=True))
    response = asyncio.run(mpesa.handle_stk_callback(callback))
    return jsonify(response.model_dump(by_alias=True))


@bp.post("/c2b/validation")
def c2b_validation():
    callback = C2BCallback.model_validate(request.get_json(force=True))
    response = asyncio.run(mpesa.handle_c2b_validation(callback))
    return jsonify(response.model_dump(by_alias=True))


@bp.post("/c2b/confirmation")
def c2b_confirmation():
    callback = C2BCallback.model_validate(request.get_json(force=True))
    response = asyncio.run(mpesa.handle_c2b_confirmation(callback))
    return jsonify(response.model_dump(by_alias=True))