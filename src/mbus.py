from pymessagebus import *
import logging
from pymessagebus.middleware.logger import get_logger_middleware
from main_events import FOAD

logger = logging.getLogger("MBus")
logging.basicConfig(level=logging.ERROR)
logging_middleware = get_logger_middleware(logger)

#FIXME: can probably just dump this in main.py
MBus = MessageBus(middlewares=[logging_middleware])