import logging
from fastapi import FastAPI
from app.endpoints.payment_router import router as payment_router
from app.database import Base, engine

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payment Service")
app.include_router(payment_router, prefix="/api/payments")

@app.on_event("startup")
async def startup_event():
    """Инициализация при старте приложения"""
    logger.info("Payment Service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие соединений при остановке"""
    logger.info("Payment Service shutting down")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "payment"}

@app.get("/")
async def root():
    return {"message": "Payment Service is running"}