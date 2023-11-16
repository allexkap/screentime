import re
from collections import Counter, OrderedDict
from dataclasses import dataclass
from pathlib import Path

import yaml


class Logs:
    def __init__(self, log_data: dict):
        log_data = OrderedDict(sorted(log_data.items()))
        dates = tuple(log_data.keys())
        self.ts_from, self.ts_to = dates[0], dates[-1]
        self.data = [Counter()] * (self.ts_to - self.ts_from + 1)
        for ts, entry in log_data.items():
            self.data[ts - self.ts_from] = Counter(entry)

    def __getitem__(self, val):
        match val:
            case int() as i:
                if i < self.ts_from or i > self.ts_to:
                    return Counter()
                return self.data[i - self.ts_from]
            case slice() as sl:
                assert sl.step is None
                return sum((self[i] for i in range(sl.start, sl.stop)), Counter())
            case _:
                raise TypeError

    def __len__(self):
        return len(self.data)


path = Path("log/")

raw = {}
for filepath in path.iterdir():
    if not re.match("\d{8}$", filepath.name):
        continue
    with open(filepath) as file:
        raw[int(filepath.name)] = yaml.load(file, yaml.SafeLoader)
