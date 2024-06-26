import asyncio
import logging
import logging.handlers
import os
from argparse import ArgumentParser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, NoReturn

import psutil
import win32api
import win32gui
import win32process

from db import Activity

logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] %(levelname)s %(filename)s:%(lineno)d %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=(
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            Path(__file__).with_suffix('.log'),
            maxBytes=2**20,
            backupCount=4,
        ),
    ),
)


def safe(default, attempts=3):
    def dec(func):
        def inner(*args, **kwargs):
            for _ in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as ex:
                    logging.warning(ex)
            logging.error(f'fallback to the default value: {default}')
            return default

        return inner

    return dec


async def lightsleep(ts: datetime) -> None:
    while True:
        now = datetime.now()
        dt = (ts - now).total_seconds()
        if dt <= 0:
            return
        await asyncio.sleep(min(1, dt))


async def repeat(func: Callable, seconds: float) -> NoReturn:
    delta = timedelta(seconds=seconds)
    ts = datetime.now()
    while True:
        ts = max(ts + delta, datetime.now())
        await lightsleep(ts)
        func()


@safe(default=0)
def get_idle_sec() -> float:
    return (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000


@safe(default='?')
def get_process_name() -> str:
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    name = psutil.Process(pid).name()
    return name


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-d',
        '--db_path',
        help='path to sqlite3 database',
        default='./db.sqlite3',
        type=Path,
    )
    parser.add_argument(
        '-u',
        '--update',
        help='interval in seconds between checking the foreground window',
        default=1,
        type=int,
    )
    parser.add_argument(
        '-c',
        '--commit',
        help='interval in seconds between saving to disk',
        default=60,
        type=int,
    )
    parser.add_argument(
        '-i',
        '--idle',
        help='interval in seconds of inactivity',
        default=30,
        type=int,
    )
    return parser.parse_args()


def update() -> None:
    idle = get_idle_sec()
    if idle <= args.idle:
        app = get_process_name()
        activity.update(app, args.update)
    else:
        app = ''
    print(f'\033[K {idle:4.0f} {app}', end='\r', flush=True)


def commit() -> None:
    activity.commit()


if __name__ == '__main__':
    args = parse_args()
    os.system('')  # enables ansi escape characters in windows terminal

    activity = Activity(args.db_path)

    loop = asyncio.new_event_loop()
    try:
        loop.create_task(repeat(update, args.update))
        loop.create_task(repeat(commit, args.commit))
        loop.run_forever()
    except Exception as ex:
        logging.critical(ex)
    finally:
        loop.close()
