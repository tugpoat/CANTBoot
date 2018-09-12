from multiprocessing import Manager
from asyncio import *

loaderq = Manager().Queue()
sysq	= Queue()
ui_webq = Queue()
ui_lcdq = Queue()
