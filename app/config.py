import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/local.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_VERSION = "0.1.0"
