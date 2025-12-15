import logging
from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
import time
import os
from pathlib import Path

from app.endpoints.payment_router import router as payment_router
from app.database import Base, engine
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, PAYMENTS_CREATED, PAYMENTS_PROCESSED, ACTIVE_PAYMENTS, DB_SIZE, \
    DB_CONNECTIONS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payment Service")
app.include_router(payment_router, prefix="/api/payments")


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code

        # Регистрируем запрос
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)

        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
        raise


def update_db_metrics():
    """Обновление метрик базы данных"""
    try:
        db_path = Path("payments.db")
        if db_path.exists():
            DB_SIZE.set(db_path.stat().st_size)

        # Здесь можно добавить логику для подсчета активных соединений
        DB_CONNECTIONS.set(1)  # Простое значение для примера

    except Exception as e:
        logger.error(f"Error updating DB metrics: {e}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "payment"}


@app.get("/")
async def root():
    return {"message": "Payment Service is running"}


@app.get("/metrics")
async def metrics():
    # Обновляем метрики базы данных
    update_db_metrics()

    registry = CollectorRegistry()
    registry.register(REQUEST_COUNT)
    registry.register(REQUEST_LATENCY)
    registry.register(PAYMENTS_CREATED)
    registry.register(PAYMENTS_PROCESSED)
    registry.register(ACTIVE_PAYMENTS)
    registry.register(DB_SIZE)
    registry.register(DB_CONNECTIONS)

    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)