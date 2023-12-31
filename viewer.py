import argparse
import itertools
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from itertools import chain
from pathlib import Path
from typing import Any, Generator, Iterable

import numpy as np
import yaml


def color2text(r: int | float, g: int | float, b: int | float, t='  ') -> str:
    if min(r, g, b) < 0:
        return t
    f = lambda v: min(max(int(v), 0), 255)
    return f'\033[48;2;{f(r)};{f(g)};{f(b)}m{t}\033[0m'


def array2text(arr: Iterable) -> tuple[str, ...]:
    return tuple(''.join(color2text(0, cell, 0) for cell in row) for row in arr)


def normalize(arr: np.ndarray) -> np.ndarray:
    top = arr.max()
    arr *= 255
    arr //= top
    return arr


def timerange(
    start: datetime, stop: datetime, step: timedelta
) -> Generator[datetime, Any, Any]:
    while start < stop:
        yield start
        start += step


def monthrange(start: datetime, stop: datetime) -> Generator[datetime, Any, Any]:
    carry = timedelta()
    while start < stop:
        yield start
        tmp = start.replace(day=1)
        step = (tmp + timedelta(days=32)).replace(day=1) - tmp
        tmp = start
        start += step + carry
        carry *= 0
        if start.month - tmp.month == 2:
            offset = timedelta(days=start.day)
            carry += offset
            start -= offset


class Logs:
    def __init__(self, path: str) -> None:
        self.logs = {}
        self._load_logs(path)

    def _load_logs(self, _path: str) -> None:
        path = Path(_path)
        if path.is_dir():
            for filename in os.listdir(path):
                if re.match(r'\d{8}$', filename):
                    with open(path / filename) as file:
                        self.logs[filename] = Counter(yaml.load(file, yaml.SafeLoader))
        else:
            with open(path) as file:
                self.logs = yaml.load(file, yaml.UnsafeLoader)

    def squeeze(self, outfile: Path) -> None:
        with open(outfile, 'w') as file:
            yaml.dump(self.logs, file)

    def __getitem__(self, index: str | datetime) -> Counter[str]:
        if isinstance(index, datetime):
            index = index.strftime(r'%y%m%d%H')

        return self.logs.get(index, Counter())


def get_rating(
    logs: Logs, start: datetime, stop: datetime
) -> tuple[tuple[str, int], ...]:
    res = sum(
        (logs[ts] for ts in timerange(start, stop, timedelta(hours=1))), Counter()
    )
    res = tuple(
        (k, v) for k, v in sorted(res.items(), key=lambda l: l[1], reverse=True) if k
    )
    return res


def gen_title(rating: tuple[tuple[str, int], ...]) -> str:
    return 'Apps: {}\nTime: {}\n'.format(
        ', '.join(app for app, _ in rating),
        timedelta(seconds=sum(score for _, score in rating)),
    )


def gen_hour_view(
    logs: Logs, apps: Iterable[str], start: datetime, stop: datetime, hour_shift=8
) -> str:
    shift = timedelta(hours=hour_shift)

    res = np.fromiter(
        chain.from_iterable(
            (
                (lambda x: sum(int(x.get(app, 0)) for app in apps))(logs[ts + shift])
                for ts in timerange(day, day + timedelta(days=1), timedelta(hours=1))
            )
            for day in timerange(start, stop, timedelta(days=1))
        ),
        dtype=int,
    )
    res.shape = -1, 24
    res = normalize(res).T

    header = '  '.join(
        ts.strftime(r'%d') for ts in timerange(start, stop, timedelta(days=2))
    )

    preheader = ''.join(
        f'{" " * max(b - a - 3, 0)}{m.strftime("%b")}'
        for m, (a, b) in zip(
            monthrange(start, stop + timedelta(days=4)),
            itertools.pairwise(
                (
                    *(0, 0),
                    *(pos.start() for pos in re.finditer(r'(?<=[1-9]\d  )0\d', header)),
                )
            ),
        )
    )

    body = '\n'.join(
        f'{(hour+hour_shift)%24:02} {line}' for hour, line in enumerate(array2text(res))
    )

    return f'   {preheader}\n   {header}\n{body}\n'


def gen_day_view(
    logs: Logs, apps: Iterable[str], start: datetime, stop: datetime, hour_shift=8
) -> str:
    start_offset = start.weekday()
    start -= timedelta(days=start_offset)
    stop_offset = -stop.weekday() % 7
    stop += timedelta(days=stop_offset)
    shift = timedelta(hours=hour_shift)

    res = np.fromiter(
        chain.from_iterable(
            (
                (
                    sum(
                        logs[ts + shift].get(app, 0)
                        for app in apps
                        for ts in timerange(
                            day, day + timedelta(days=1), timedelta(hours=1)
                        )
                    )
                    for day in timerange(
                        week, week + timedelta(days=7), timedelta(days=1)
                    )
                )
                for week in timerange(
                    start,
                    stop,
                    timedelta(days=7),
                )
            )
        ),
        dtype=int,
    )
    res.shape = -1, 7
    res = normalize(res).T

    res[:start_offset, 0] = -1
    res[res.shape[0] - stop_offset :, -1] = -1

    header_offset = '      ' if start_offset else '    '

    header_start = start
    if start_offset:
        header_start += timedelta(days=7)
    header = '  '.join(
        ts.strftime(r'%d') for ts in timerange(header_start, stop, timedelta(days=14))
    )

    preheader = ''.join(
        f'{" " * max(b - a - 3, 0)}{m.strftime("%b")}'
        for m, (a, b) in zip(
            monthrange(header_start, stop + timedelta(days=32)),
            itertools.pairwise(
                (
                    *(0, 0),
                    *(
                        pos.start()
                        for pos in re.finditer(
                            r'(?<=[123]\d  )0\d|(?<=[23]\d  )1\d', header
                        )
                    ),
                )
            ),
        )
    )

    weekdays = ('Mon', '   ', 'Wed', '   ', 'Fri', '   ', 'Sun')  # o_o
    body = '\n'.join(f'{weekdays[n]} {line}' for n, line in enumerate(array2text(res)))

    return f'{header_offset}{preheader}\n{header_offset}{header}\n{body}\n'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', required=True)
    parser.add_argument('-f', '--from', dest='start', type=datetime.fromisoformat)
    parser.add_argument('-t', '--to', dest='stop', type=datetime.fromisoformat)
    parser.add_argument('-r', '--rank', type=int)
    parser.add_argument('-o', '--out')

    args = parser.parse_args()
    if (not args.start or not args.stop) and not args.out:
        parser.error(
            'the following arguments are required: (--from and --to) or --out '
        )

    return args


def non_interactive_mode(logs: Logs, args: argparse.Namespace) -> None:
    rating = get_rating(logs, args.start, args.stop)[args.rank : args.rank + 1]
    apps = tuple(app for app, _ in rating)

    print(gen_title(rating))
    print(gen_day_view(logs, apps, args.start, args.stop), end='')


def interactive_mode(logs: Logs, args: argparse.Namespace) -> None:
    from getkey import getkey, keys

    args.rank = 0
    rating = get_rating(logs, args.start, args.stop)
    print('\033[s', end='')
    while True:
        print('\033[u\033[J', end='')
        non_interactive_mode(logs, args)
        match getkey():
            case keys.UP:
                args.rank = max(args.rank - 1, 0)
            case keys.DOWN:
                args.rank = min(args.rank + 1, len(rating) - 1)


if __name__ == '__main__':
    args = parse_args()

    logs = Logs(args.path)
    if args.out:
        logs.squeeze(args.out)
        exit()

    if args.rank is not None:
        non_interactive_mode(logs, args)
    else:
        try:
            interactive_mode(logs, args)
        except KeyboardInterrupt:
            pass
