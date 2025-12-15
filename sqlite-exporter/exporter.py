#!/usr/bin/env python3
"""
SQLite Exporter для Prometheus
"""
import os
import sqlite3
import time
from http.server import HTTPServer
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

# Получаем путь к базе данных из переменной окружения
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', '/app/payments.db')

# Создаем метрики Prometheus
DB_SIZE = Gauge('sqlite_db_size_bytes', 'Size of SQLite database file in bytes')
TABLE_COUNT = Gauge('sqlite_table_count', 'Number of tables in the database')
ROW_COUNT = Gauge('sqlite_table_rows', 'Number of rows in table', ['table'])
TABLE_SIZE = Gauge('sqlite_table_size_kb', 'Estimated table size in KB', ['table'])


def collect_metrics():
    """Сбор метрик из SQLite базы данных"""
    try:
        # Размер файла базы данных
        if os.path.exists(SQLITE_DB_PATH):
            DB_SIZE.set(os.path.getsize(SQLITE_DB_PATH))
        else:
            DB_SIZE.set(0)
            print(f"Database file not found: {SQLITE_DB_PATH}")
            return

        # Подключаемся к базе данных
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Количество таблиц
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        TABLE_COUNT.set(cursor.fetchone()[0])

        # Информация о таблицах
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()

        for (table_name,) in tables:
            # Количество строк в таблице
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                ROW_COUNT.labels(table=table_name).set(row_count)

                # Примерный размер таблицы (очень грубая оценка)
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                estimated_size = row_count * len(columns) * 100  # ~100 байт на запись
                TABLE_SIZE.labels(table=table_name).set(estimated_size / 1024)  # в KB
            except Exception as e:
                print(f"Error processing table {table_name}: {e}")

        conn.close()

    except Exception as e:
        print(f"Error collecting metrics: {e}")


class MetricsHandler:
    def do_GET(self):
        collect_metrics()

        self.send_response(200)
        self.send_header('Content-Type', CONTENT_TYPE_LATEST)
        self.end_headers()

        self.wfile.write(generate_latest())


if __name__ == '__main__':
    print(f"Starting SQLite Exporter on port 8082 for database: {SQLITE_DB_PATH}")

    # Создаем простой HTTP сервер
    from http.server import BaseHTTPRequestHandler
    import socketserver


    class Handler(BaseHTTPRequestHandler, MetricsHandler):
        pass


    server = HTTPServer(('0.0.0.0', 8082), Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down SQLite Exporter")
        server.server_close()