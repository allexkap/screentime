import asyncio
import logging
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
        logging.FileHandler(Path(__file__).with_suffix('.log'), 'a'),
        logging.StreamHandler(),
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
            return default

        return inner

    return dec


async def lightsleep(seconds: float) -> None:
    date = datetime.now() + timedelta(seconds=seconds)
    while datetime.now() < date:
        await asyncio.sleep(1)


async def repeat(func: Callable, seconds: float, now=False) -> NoReturn:
    delta = seconds if not now else 0
    while True:
        await lightsleep(delta)
        delta = func()
        if delta is None:
            delta = seconds


@safe(default=0, attempts=1)
def get_idle_sec() -> int:
    return win32api.GetTickCount() - win32api.GetLastInputInfo()


@safe(default='?', attempts=1)
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
    return parser.parse_args()


def update():
    app = get_process_name()
    activity.update(app, 1)


def commit():
    activity.commit()


if __name__ == '__main__':
    args = parse_args()

    activity = Activity(args.db_path)

    loop = asyncio.new_event_loop()
    try:
        loop.create_task(repeat(update, 1))
        loop.create_task(repeat(commit, 60))
        loop.run_forever()
    except Exception as ex:
        logging.critical(ex)
    finally:
        loop.close()
