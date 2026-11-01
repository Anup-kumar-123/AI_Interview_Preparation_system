import logging
import os
from dotenv import load_dotenv

load_dotenv()


def setup_logger(name: str = "PrepPulseAI") -> logging.Logger:
    """Configures system-wide logging standard."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, log_level, logging.INFO))

    return logger


logger = setup_logger()
