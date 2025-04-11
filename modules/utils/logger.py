import logging


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging with the given level."""
    logging.basicConfig(level=level)
