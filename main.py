import win32api
import win32gui
import win32process
import psutil


def safe(default, handler=lambda e: None):
    def dec(func):
        def inner(*args, **kwargs):
            try:
                return func()
            except Exception as e:
                handler(e)
                return default
        return inner
    return dec


def handler(e):
    print('Warning:', e)

@safe(0, handler)
def getIdleSec():
    return win32api.GetTickCount() - win32api.GetLastInputInfo()

@safe(None, handler)
def getProcessName():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    name = psutil.Process(pid).name()
    return name


import asyncio
from observer import Observer

try:
    asyncio.run(Observer(watch=getProcessName, idle=getIdleSec, path='log').observe())
except Exception as e:
    input('Critical:', e)
