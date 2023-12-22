import enum
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
    f = lambda v: min(max(int(v), 0), 255)
    return f'\033[48;2;{f(r)};{f(g)};{f(b)}m{t}\033[0m'


def array2text(arr):
    return tuple(''.join(color2text(0, cell, 0) for cell in row) for row in arr)


def norm(arr):
    arr *= 255
    arr //= arr.max() // 255
    return arr


def timerange(start: datetime, stop: datetime, step: timedelta):
    while start < stop:
        yield start
        start += step


def monthrange(start: datetime, stop: datetime):
    while start < stop:
        yield start
        tmp = start.replace(day=1)
        step = (tmp + timedelta(days=32)).replace(day=1) - tmp
        start += step


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
        if isinstance(index, slice):
            if isinstance(index.step, timedelta):
                step = index.step
            else:
                step = timedelta(hours=1)

            return sum(
                (self[ts] for ts in timerange(index.start, index.stop, step)),
                Counter(),
            )

        if isinstance(index, datetime):
            index = index.strftime(r'%y%m%d%H')

        return self.logs.get(index, Counter())


def gen_hour_view(logs, apps, start, stop, hour_shift=8):
    res = np.fromiter(
        chain.from_iterable(
            (
                sum(logs[ts].get(app, 0) for app in apps)
                for ts in timerange(day, day + timedelta(days=1), timedelta(hours=1))
            )
            for day in timerange(start, stop, timedelta(days=1))
        ),
        dtype=int,
    )
    res.shape = -1, 24
    res = np.roll(res, -hour_shift)
    res = norm(res).T

    header = '  '.join(
        ts.strftime(r'%d') for ts in timerange(start, stop, timedelta(days=2))
    )
    preheader = ''.join(
        f'{" " * max(b - a - 3, 0)}{m.strftime("%b")}'
        for m, (a, b) in zip(
            monthrange(dates[0], dates[1]),
            itertools.pairwise(
                (
                    *(0, 0),
                    *(pos.start() for pos in re.finditer('(?<=[1-9]\d  )0\d', header)),
                )
            ),
        )
    )
    body = '\n'.join(
        f'{(hour+hour_shift)%24:02} {line}' for hour, line in enumerate(array2text(res))
    )
    return f'   {preheader}\n   {header}\n{body}\n'
