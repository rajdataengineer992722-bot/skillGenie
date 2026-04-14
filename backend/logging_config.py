import logging
from logging.config import dictConfig

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings


def configure_logging():
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"}
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "default"}
            },
            "root": {"handlers": ["console"], "level": settings.log_level},
        }
    )
    return logging.getLogger(settings.app_name)
