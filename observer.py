import asyncio
import logging
import logging.handlers
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


async def lightsleep(seconds: float) -> None:
    date = datetime.now() + timedelta(seconds=seconds)
    while datetime.now() < date:
        await asyncio.sleep(1)


async def repeat(func: Callable, seconds: float) -> NoReturn:
    while True:
        await lightsleep(seconds)
        func()


@safe(default=0)
def get_idle_sec() -> int:
    return win32api.GetTickCount() - win32api.GetLastInputInfo()


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
    if get_idle_sec() > args.idle:
        return
    app = get_process_name()
    activity.update(app, args.update)


def commit() -> None:
    activity.commit()


if __name__ == '__main__':
    args = parse_args()

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
