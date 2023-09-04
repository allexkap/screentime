import win32api
import win32gui
import win32process
import psutil


def get_idle_sec():
    return win32api.GetTickCount() - win32api.GetLastInputInfo()

def getProcessName():
    try:
        if get_idle_sec() > 30_000:
            return None
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        name = psutil.Process(pid).name()
        return name
    except Exception as e:
        print('Warning:', e)
        return None


import asyncio
from observer import Observer

try:
    asyncio.run(Observer(func=getProcessName, path='log').observe())
except Exception as e:
    input('Critical:', e)
