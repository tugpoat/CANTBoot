from pymessagebus import *
import logging
from pymessagebus.middleware.logger import get_logger_middleware

logger = logging.getLogger("MBus")
logging.basicConfig(level=logging.DEBUG)
logging_middleware = get_logger_middleware(logger)

#FIXME: can probably just dump this in main.py
MBus = MessageBus(middlewares=[logging_middleware])
