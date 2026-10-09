from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from singularity_payments import (
    AccountBalanceCallback,
    B2BCallback,
    B2CCallback,
    C2BCallback,
    ReversalCallback,
    STKCallback,
    STKPushRequest,
    TransactionStatusCallback,
)

from .mpesa import mpesa


class STKPushPayload(BaseModel):
    amount: float
    phone_number: str
    account_reference: str = "INV-001"
    transaction_desc: str = "Payment for order"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    mpesa.destroy()  # stop the background rate-limiter cleanup task


app = FastAPI(lifespan=lifespan)


@app.post("/api/mpesa/stk-push")
async def stk_push(payload: STKPushPayload):
    response = await mpesa.stk_push(
        STKPushRequest(
            amount=payload.amount,
            phone_number=payload.phone_number,
            account_reference=payload.account_reference,
            transaction_desc=payload.transaction_desc,
        )
    )
    return response


@app.post("/api/mpesa/callback")
async def stk_callback(request: Request):
    body = await request.json()
    response = await mpesa.handle_stk_callback(STKCallback.model_validate(body))
    return response.model_dump(by_alias=True)


@app.post("/api/mpesa/c2b/validation")
async def c2b_validation(request: Request):
    body = await request.json()
    response = await mpesa.handle_c2b_validation(C2BCallback.model_validate(body))
    return response.model_dump(by_alias=True)


@app.post("/api/mpesa/c2b/confirmation")
async def c2b_confirmation(request: Request):
    body = await request.json()
    response = await mpesa.handle_c2b_confirmation(C2BCallback.model_validate(body))
    return response.model_dump(by_alias=True)


@app.post("/api/mpesa/b2c/result")
async def b2c_result(request: Request):
    body = await request.json()
    response = await mpesa.handle_b2c_callback(B2CCallback.model_validate(body))
    return response.model_dump(by_alias=True)


@app.post("/api/mpesa/b2b/result")
async def b2b_result(request: Request):
    body = await request.json()
    response = await mpesa.handle_b2b_callback(B2BCallback.model_validate(body))
    return response.model_dump(by_alias=True)


@app.post("/api/mpesa/balance/result")
async def balance_result(request: Request):
    body = await request.json()
    response = await mpesa.handle_account_balance_callback(
        AccountBalanceCallback.model_validate(body)
    )
    return response.model_dump(by_alias=True)


@app.post("/api/mpesa/status/result")
async def status_result(request: Request):
    body = await request.json()
    response = await mpesa.handle_transaction_status_callback(
        TransactionStatusCallback.model_validate(body)
    )
    return response.model_dump(by_alias=True)


@app.post("/api/mpesa/reversal/result")
async def reversal_result(request: Request):
    body = await request.json()
    response = await mpesa.handle_reversal_callback(ReversalCallback.model_validate(body))
    return response.model_dump(by_alias=True)