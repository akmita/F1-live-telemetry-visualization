import logging
import threading

# Configure the logger once at program start
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)

# Create a lock for explicit thread safety (though logging is thread-safe by default)
log_lock = threading.Lock()

def safe_log(level, *args, **kwargs):
    """Thread-safe logging wrapper."""
    with log_lock:
        message = " ".join(str(a) for a in args)
        logging.log(level, message, **kwargs)

def log_info(*args, **kwargs):
    safe_log(logging.INFO, *args, **kwargs)

def log_debug(*args, **kwargs):
    safe_log(logging.DEBUG, *args, **kwargs)