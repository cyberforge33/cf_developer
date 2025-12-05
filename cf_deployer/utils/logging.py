import logging

def setup_logger(name: str, level=logging.INFO, fmt: str = None) -> logging.Logger:
    """
    Configure a logger with consistent formatting.
    """
    fmt = fmt or "%(asctime)s - %(levelname)s - %(message)s"
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.hasHandlers():
        logger.addHandler(handler)
    return logger
