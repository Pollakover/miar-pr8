import asyncio
import logging
from fastapi import FastAPI
from app.endpoints.notification_router import router as notification_router
from app.consumers.notification_consumer import NotificationConsumer
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service")
app.include_router(notification_router, prefix="/api/notifications")

# Глобальная переменная для хранения consumer
notification_consumer = None
consumer_thread = None

def start_consumer():
    """Запуск потребителя в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    consumer = NotificationConsumer()

    try:
        loop.run_until_complete(consumer.start_consuming())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Consumer stopped with error: {e}")
    finally:
        loop.run_until_complete(consumer.close())
        loop.close()

@app.on_event("startup")
async def startup_event():
    """Запуск потребителя при старте приложения"""
    global consumer_thread

    # Запускаем consumer в отдельном потоке, чтобы не блокировать FastAPI
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("Notification consumer started in background thread")

@app.on_event("shutdown")
async def shutdown_event():
    """Остановка приложения"""
    logger.info("Shutting down Notification Service")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "notification",
        "consumer_alive": consumer_thread.is_alive() if consumer_thread else False
    }