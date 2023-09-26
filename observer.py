import os
import time
import yaml
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field


async def lightsleep(seconds):
    date = datetime.now() + timedelta(seconds=seconds)
    while datetime.now() < date:
        await asyncio.sleep(1)

async def repeat(func, arg):
    res = None
    while True:
        await lightsleep(res or (arg() if callable(arg) else arg))
        res = func()

def until00min():
    now = time.localtime()
    return (60 - now.tm_min) * 60 + now.tm_sec


@dataclass
class Cache:
    path: str
    score: dict[str, int] = field(default_factory=dict)


class Observer:

    def __init__(self, watch, idle, path='.', interval={}, pattern='%y%m%d%H'):
        self.watch = watch
        self.idle = idle
        self.path = path
        self.pattern = pattern
        self.interval = {
            'update': 1,
            'commit': 10*60,
            'idle': 60,
        }
        self.interval.update(interval)
        self.cache = self.loadCache()
        self.is_active = True

    def loadCache(self):
        path = f'{self.path}/{time.strftime(self.pattern, time.localtime())}'
        if not os.path.exists(path):
            return Cache(path)
        with open(path) as file:
            return Cache(path, yaml.load(file.read(), yaml.Loader))

    def reload(self):
        self.commit()
        self.cache = self.loadCache()

    def update(self):
        if not self.is_active:
            return
        window = self.watch()
        if window not in self.cache.score:
            self.cache.score[window] = 0
        self.cache.score[window] += self.interval['update']

    def commit(self):
        with open(self.cache.path, 'w') as file:
            file.write(yaml.dump(self.cache.score))

    def checkActivity(self):
        sec = self.idle()
        if sec < self.interval['idle']:
            self.is_active = True
            return self.interval['idle'] - sec + 1
        self.is_active = False

    async def observe(self):
        coros = (
            repeat(self.update, arg=self.interval['update']),
            repeat(self.commit, arg=self.interval['commit']),
            repeat(self.reload, arg=until00min),
            repeat(self.checkActivity, arg=1),
        )
        await asyncio.gather(*coros)
