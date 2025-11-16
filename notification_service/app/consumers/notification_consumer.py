import aio_pika
import json
import asyncio
import os
from uuid import uuid4
from datetime import datetime
from app.services.notification_service import NotificationService
from app.models.notification import Notification, NotificationType, NotificationStatus
import logging

logger = logging.getLogger(__name__)

class NotificationConsumer:
    def __init__(self):
        self.connection_string = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.notification_service = NotificationService()
        self.connection = None
        self.channel = None
        self._max_retries = 10
        self._retry_delay = 5

    async def connect(self):
        """Установка соединения с RabbitMQ с повторными попытками"""
        for attempt in range(self._max_retries):
            try:
                logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{self._max_retries})")
                self.connection = await aio_pika.connect_robust(self.connection_string)
                self.channel = await self.connection.channel()

                # Устанавливаем QoS для обработки одного сообщения за раз
                await self.channel.set_qos(prefetch_count=1)

                # Объявляем exchange
                exchange = await self.channel.declare_exchange(
                    "notifications",
                    aio_pika.ExchangeType.FANOUT,
                    durable=True
                )

                # Объявляем очередь для уведомлений
                queue = await self.channel.declare_queue(
                    "payment_notifications",
                    durable=True
                )

                await queue.bind(exchange)

                logger.info("Successfully connected to RabbitMQ")
                return queue

            except Exception as e:
                logger.warning(f"Failed to connect to RabbitMQ: {e}")
                if attempt < self._max_retries - 1:
                    logger.info(f"Retrying in {self._retry_delay} seconds...")
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error("Max retries exceeded, cannot connect to RabbitMQ")
                    raise

    async def start_consuming(self):
        """Запуск потребителя"""
        try:
            queue = await self.connect()
            logger.info("Starting to consume messages...")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            await self.process_message(message.body)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Consumer stopped due to error: {e}")
            # Можно добавить логику перезапуска

    async def process_message(self, body: bytes):
        """Обработка входящего сообщения"""
        try:
            message_data = json.loads(body.decode())
            logger.info(f"Received message: {message_data}")

            # Создаем уведомление на основе полученных данных
            notification_type = NotificationType(message_data.get("type", "order_placed"))
            message_text = message_data.get("message", "Payment completed")

            created_notification = self.notification_service.send(
                n_type=notification_type,
                message=message_text,
                recipient=None
            )

            logger.info(f"Notification created: {created_notification.id}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing notification: {e}")

    async def close(self):
        """Закрытие соединения"""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")