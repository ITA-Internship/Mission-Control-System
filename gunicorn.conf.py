"""Gunicorn configuration file.

All tunables are read from environment variables so the same image
works unchanged across local development and production.
"""

import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "15"))
keepalive = int(os.getenv("GUNICORN_KEEP_ALIVE", "5"))
accesslog = "-"
errorlog = "-"
