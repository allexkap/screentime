import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import yaml


async def lightsleep(seconds):
    date = datetime.now() + timedelta(seconds=seconds)
    while datetime.now() < date:
        await asyncio.sleep(1)


async def repeat(func, arg):
    res = None
    while True:
        await lightsleep(res or (arg() if callable(arg) else arg))
        res = func()


@dataclass
class Cache:
    path: str
    timestamp: float
    score: dict[str, int] = field(default_factory=dict)


class Observer:
    def __init__(self, watch, idle, path='.', intervals={}, pattern=r'%y%m%d%H'):
        self.watch = watch
        self.idle = idle
        self.path = path
        self.pattern = pattern
        self.intervals = {
            'update': 1,
            'commit': 60,
            'idle': 60,
        }
        self.intervals.update(intervals)
        self.cache = self.loadCache()
        self.is_active = True

    def loadCache(self):
        timestamp = datetime.now()
        ts = timestamp.timestamp() // 3600
        path = f'{self.path}/{timestamp.strftime(self.pattern)}'
        if not os.path.exists(path):
            return Cache(path, ts)
        with open(path) as file:
            return Cache(path, ts, yaml.load(file.read(), yaml.Loader))

    def validateCache(self):
        if datetime.now().timestamp() // 3600 != self.cache.timestamp:
            self.commit()
            self.cache = self.loadCache()

    def update(self):
        self.validateCache()
        if not self.is_active:
            return
        window = self.watch()
        if window not in self.cache.score:
            self.cache.score[window] = 0
        self.cache.score[window] += self.intervals['update']

    def commit(self):
        with open(self.cache.path, 'w') as file:
            file.write(yaml.dump(self.cache.score))

    def checkActivity(self):
        sec = self.idle()
        if sec < self.intervals['idle']:
            self.is_active = True
            return self.intervals['idle'] - sec
        self.is_active = False

    async def observe(self):
        coros = (
            repeat(self.update, arg=self.intervals['update']),
            repeat(self.commit, arg=self.intervals['commit']),
            repeat(self.checkActivity, arg=1),
        )
        await asyncio.gather(*coros)
