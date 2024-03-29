import asyncio

import psutil
import win32api
import win32gui
import win32process

from observer import Observer


def safe(default, handler=lambda e: None):
    def dec(func):
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                handler(ex)
                return default

        return inner

    return dec


def handler(ex):
    print('Warning:', ex)


@safe(0, handler)
def getIdleSec():
    return win32api.GetTickCount() - win32api.GetLastInputInfo()


@safe(None, handler)
def getProcessName():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    name = psutil.Process(pid).name()
    return name


try:
    asyncio.run(Observer(watch=getProcessName, idle=getIdleSec, path='./log').observe())
except Exception as ex:
    print('Critical:', ex)
    input()
