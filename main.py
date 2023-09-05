import win32api
import win32gui
import win32process
import psutil


def getIdleSec():
    try:
        return win32api.GetTickCount() - win32api.GetLastInputInfo()
    except Exception as e:
        print('Warning:', e)
        return 0

def getProcessName():
    try:
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
    asyncio.run(Observer(watch=getProcessName, idle=getIdleSec, path='log').observe())
except Exception as e:
    input('Critical:', e)
