from win32api import GetLastInputInfo, GetTickCount

import asyncio


DELAY = 60  # minute

_is_active = False


def get_idle_sec():
    return (GetTickCount() - GetLastInputInfo()) / 1000

async def update():
    idle = get_idle_sec()
    while True:
        if idle < DELAY:
            _is_active = False
            await asyncio.sleep(DELAY - idle)
        else:
            _is_active = True
        await asyncio.sleep(1)


def is_active():
    return _is_active
