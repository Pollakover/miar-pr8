"""
Metrics for Notification Service
"""
from prometheus_client import Counter, Histogram, Gauge

# Создаем метрики Prometheus
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

NOTIFICATIONS_SENT = Counter(
    'notifications_sent_total',
    'Total number of notifications sent',
    ['type', 'status']
)

NOTIFICATIONS_QUEUED = Gauge(
    'notifications_queued',
    'Number of notifications in queue'
)

RABBITMQ_CONNECTIONS = Gauge(
    'rabbitmq_connections',
    'RabbitMQ connection status'
)