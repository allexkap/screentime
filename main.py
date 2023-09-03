import win32api
import win32gui
import win32process
import psutil


def get_idle_sec():
    return win32api.GetTickCount() - win32api.GetLastInputInfo()

def getProcessName():
    if get_idle_sec > 30_000:
        return None
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    name = psutil.Process(pid).name()
    return name


import asyncio
from observer import Observer

asyncio.run(Observer(func=getProcessName, path='log').run())
