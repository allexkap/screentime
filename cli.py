import argparse
import itertools
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from itertools import chain
from pathlib import Path

import numpy as np
import yaml


def color2text(r, g, b, t='  '):
    if min(r, g, b) < 0:
        return t
    f = lambda v: min(max(int(v), 0), 255)
    return f'\033[48;2;{f(r)};{f(g)};{f(b)}m{t}\033[0m'


def array2text(arr):
    return tuple(''.join(color2text(0, cell, 0) for cell in row) for row in arr)


def normalize(arr):
    arr *= 255
    arr //= arr.max() // 255
    return arr


def timerange(start: datetime, stop: datetime, step: timedelta):
    while start < stop:
        yield start
        start += step


def monthrange(start: datetime, stop: datetime):
    day = timedelta(days=1)
    carry = timedelta()
    while start < stop:
        yield start
        tmp = start.replace(day=1)
        step = (tmp + timedelta(days=32)).replace(day=1) - tmp
        tmp = start
        start += step
        while carry.days:
            start += carry
            carry -= day
        while start.month - tmp.month == 2:
            carry += day
            start -= day


class Logs:
    def __init__(self, path: Path) -> None:
        self.logs = {}
        self.load_logs(path)

    def load_logs(self, path: str) -> None:
        path = Path(path)
        # if path.is_file():
        #     with open(path) as file:
        #         return yaml.load(file, yaml.SafeLoader)
        for filename in os.listdir(path):
            if re.match('\d{8}$', filename):
                with open(path / filename) as file:
                    self.logs[filename] = Counter(yaml.load(file, yaml.SafeLoader))

    # def squeeze(self, outfile: Path) -> None:
    #     with open(outfile, 'w') as file:
    #         file.write(yaml.dump(self.logs))

    def __getitem__(self, index):
        if isinstance(index, datetime):
            index = index.strftime(r'%y%m%d%H')

        return self.logs.get(index, Counter())


def get_rating(logs, start, stop):
    res = sum(
        (logs[ts] for ts in timerange(start, stop, timedelta(hours=1))), Counter()
    )
    res = tuple(
        (k, v) for k, v in sorted(res.items(), key=lambda l: l[1], reverse=True)
    )
    return res


def gen_title(rating):
    return 'Apps: {}\nTime: {}\n'.format(
        ', '.join(app for app, _ in rating),
        timedelta(seconds=sum(score for _, score in rating)),
    )


def gen_hour_view(logs, apps, start, stop, hour_shift=8):
    shift = timedelta(hours=hour_shift)

    res = np.fromiter(
        chain.from_iterable(
            (
                (lambda x: sum(x.get(app, 0) for app in apps))(logs[ts + shift])
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


def gen_day_view(logs, apps, start, stop, hour_shift=8):
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', required=True)
    parser.add_argument(
        '-f', '--from', dest='start', type=datetime.fromisoformat, required=True
    )
    parser.add_argument(
        '-t', '--to', dest='stop', type=datetime.fromisoformat, required=True
    )
    parser.add_argument('-r', '--rank', type=int, required=True)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    logs = Logs(args.path)
    rating = get_rating(logs, args.start, args.stop)[args.rank : args.rank + 1]
    apps = tuple(app for app, _ in rating)

    print(gen_title(rating))
    print(gen_day_view(logs, apps, args.start, args.stop), end='')
