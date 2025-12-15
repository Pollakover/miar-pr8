import logging
import asyncio
from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
import time

from app.endpoints.notification_router import router as notification_router
from app.consumers.notification_consumer import NotificationConsumer
import threading
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, NOTIFICATIONS_SENT, NOTIFICATIONS_QUEUED, RABBITMQ_CONNECTIONS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service")
app.include_router(notification_router, prefix="/api/notifications")


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)

        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
        raise


# Глобальная переменная для хранения consumer
notification_consumer = None
consumer_thread = None


def start_consumer():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    consumer = NotificationConsumer()

    try:
        loop.run_until_complete(consumer.start_consuming())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Consumer error: {e}")
    finally:
        loop.run_until_complete(consumer.close())
        loop.close()


@app.on_event("startup")
async def startup_event():
    global consumer_thread

    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()

    # Устанавливаем метрику подключения к RabbitMQ
    RABBITMQ_CONNECTIONS.set(1)
    logger.info("Notification consumer started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Notification Service shutting down")


@app.get("/health")
async def health_check():
    rabbitmq_status = "connected" if RABBITMQ_CONNECTIONS._value.get() == 1 else "disconnected"
    return {
        "status": "healthy",
        "service": "notification",
        "rabbitmq": rabbitmq_status
    }


@app.get("/")
async def root():
    return {"message": "Notification Service is running"}


@app.get("/metrics")
async def metrics():
    registry = CollectorRegistry()
    registry.register(REQUEST_COUNT)
    registry.register(REQUEST_LATENCY)
    registry.register(NOTIFICATIONS_SENT)
    registry.register(NOTIFICATIONS_QUEUED)
    registry.register(RABBITMQ_CONNECTIONS)

    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)