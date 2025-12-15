"""
Metrics for Payment Service
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

PAYMENTS_CREATED = Counter(
    'payments_created_total',
    'Total number of payments created'
)

PAYMENTS_PROCESSED = Counter(
    'payments_processed_total',
    'Total number of payments processed',
    ['status']
)

ACTIVE_PAYMENTS = Gauge(
    'active_payments',
    'Number of active payments'
)

# SQLite метрики
DB_SIZE = Gauge(
    'sqlite_db_size_bytes',
    'SQLite database size in bytes'
)

DB_CONNECTIONS = Gauge(
    'sqlite_active_connections',
    'Number of active SQLite connections'
)

# Функция для получения метрик
def get_payment_metrics():
    return {
        'payments_created': PAYMENTS_CREATED,
        'payments_processed': PAYMENTS_PROCESSED,
        'active_payments': ACTIVE_PAYMENTS
    }