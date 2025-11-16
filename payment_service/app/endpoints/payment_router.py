from fastapi import APIRouter, Depends, HTTPException, Body
from uuid import UUID
from app.services.payment_service import PaymentService, CreatePaymentRequest
from app.models.payment import Payment
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_service() -> PaymentService:
    return PaymentService()

@router.get("/", response_model=list[Payment])
def list_payments(service: PaymentService = Depends(get_service)):
    return service.list_payments()

@router.post("/", response_model=Payment)
def create_payment(req: CreatePaymentRequest, service: PaymentService = Depends(get_service)):
    return service.create_payment(amount=req.amount, currency=req.currency or "USD")

@router.post("/{payment_id}/process", response_model=Payment)
async def process_payment(payment_id: UUID, success: bool = Body(embed=True), service: PaymentService = Depends(get_service)):
    try:
        result = await service.process_payment(payment_id, success)
        logger.info(f"Payment {payment_id} processed successfully")
        return result
    except KeyError:
        logger.error(f"Payment {payment_id} not found")
        raise HTTPException(status_code=404, detail="Payment not found")
    except ValueError as e:
        logger.error(f"Value error processing payment {payment_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error processing payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{payment_id}/refund", response_model=Payment)
def request_refund(payment_id: UUID, service: PaymentService = Depends(get_service)):
    try:
        return service.request_refund(payment_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Payment not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{payment_id}/refund/complete", response_model=Payment)
def complete_refund(payment_id: UUID, success: bool = Body(embed=True), service: PaymentService = Depends(get_service)):
    try:
        return service.complete_refund(payment_id, success)
    except KeyError:
        raise HTTPException(status_code=404, detail="Payment not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))