import os
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import yaml


def color2text(r, g, b, t='  '):
    f = lambda v: min(max(int(v), 0), 255)
    return f'\033[48;2;{f(r)};{f(g)};{f(b)}m{t}\033[0m'


def array2text(arr):
    return '\n'.join(''.join(color2text(0, cell, 0) for cell in row) for row in arr)


def norm(arr):
    return (arr / arr.max() * 255).astype(int)


def timerange(start: datetime, stop: datetime, step: timedelta):
    while start < stop:
        yield start
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


def gen_detail_view(logs, start, stop):
    for day in timerange(start, stop, timedelta(days=1)):
        for ts in timerange(day, day + timedelta(days=1), timedelta(hours=1)):
            pass
