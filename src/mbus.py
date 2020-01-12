from pymessagebus import *
import logging
from pymessagebus.middleware.logger import get_logger_middleware

logger = logging.getLogger("message_bus")
logging.basicConfig(level=logging.INFO)
logging_middleware = get_logger_middleware(logger)

#FIXME: can probably just dump this in main.py
MBus = MessageBus(middlewares=[logging_middleware])
