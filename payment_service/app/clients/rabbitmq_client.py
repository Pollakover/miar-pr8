import aio_pika
import json
import asyncio
from uuid import UUID
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection_string = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self._connection: Optional[aio_pika.Connection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._lock = asyncio.Lock()
        self._max_retries = 5
        self._retry_delay = 2

    async def _ensure_connection(self):
        """Обеспечивает наличие активного соединения"""
        async with self._lock:
            if self._connection and not self._connection.is_closed:
                return

            for attempt in range(self._max_retries):
                try:
                    logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{self._max_retries})")
                    self._connection = await aio_pika.connect_robust(self.connection_string)
                    self._channel = await self._connection.channel()

                    self._exchange = await self._channel.declare_exchange(
                        "notifications",
                        aio_pika.ExchangeType.FANOUT,
                        durable=True
                    )

                    # Объявляем очередь для уведомлений
                    queue = await self._channel.declare_queue(
                        "payment_notifications",
                        durable=True
                    )
                    await queue.bind(self._exchange)

                    logger.info("Successfully connected to RabbitMQ")
                    return

                except Exception as e:
                    logger.warning(f"Failed to connect to RabbitMQ: {e}")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(self._retry_delay)
                    else:
                        logger.error("Max retries exceeded, cannot connect to RabbitMQ")
                        raise

    async def send_payment_notification(self, payment_id: UUID, message_type: str = "payment_complete"):
        """Отправка сообщения о успешном платеже"""
        try:
            await self._ensure_connection()

            message_body = {
                "type": message_type,
                "payment_id": str(payment_id),
                "message": f"Payment {payment_id} completed successfully"
            }

            message = aio_pika.Message(
                body=json.dumps(message_body).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            await self._exchange.publish(message, routing_key="")
            logger.info(f"Notification sent for payment {payment_id}")

        except Exception as e:
            logger.error(f"Failed to send notification for payment {payment_id}: {e}")
            # Не выбрасываем исключение, чтобы не ломать основной процесс

    async def close(self):
        """Закрытие соединения"""
        if self._connection:
            await self._connection.close()
            logger.info("RabbitMQ connection closed")