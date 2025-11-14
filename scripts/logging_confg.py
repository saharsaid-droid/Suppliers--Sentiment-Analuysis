# logger_config.py
import logging
import os


def setup_logger(script_name):
    # Create logs folder if not exists
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Log file path
    log_file = os.path.join(log_dir, "app.log")

    # Create logger
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate logs
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler (for terminal output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Log message format
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
