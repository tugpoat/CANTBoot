from multiprocessing import Manager
from asyncio import *

loaderq = Manager().Queue()
sysq	= Manager().Queue()
ui_webq = Manager().Queue()
ui_lcdq = Manager().Queue()
