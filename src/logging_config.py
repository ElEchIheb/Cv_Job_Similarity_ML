import logging
import sys
import contextvars
import uuid

# Context variable for request IDs
request_id_ctx = contextvars.ContextVar('request_id', default='system')

class RequestIdFilter(logging.Filter):
    """Filter that injects request_id into the log record."""
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True

def setup_logging(log_level_str="INFO"):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level_str.upper(), logging.INFO))
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    
    # Add our custom filter
    handler.addFilter(RequestIdFilter())
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | req:%(request_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Suppress verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def set_request_id(req_id=None):
    if req_id is None:
        req_id = str(uuid.uuid4())[:8]
    request_id_ctx.set(req_id)
    return req_id
