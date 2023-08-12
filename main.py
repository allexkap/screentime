import win32gui
import win32process
import psutil

def getProcessName():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    name = psutil.Process(pid).name()
    return name


import asyncio
from observer import Observer

asyncio.run(Observer(func=getProcessName, path='log').run())
