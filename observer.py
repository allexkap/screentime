import os
import time
import yaml
import asyncio
from dataclasses import dataclass, field


async def repeat(func, delay, wait=0):
    if wait:
        await asyncio.sleep(wait)
    while True:
        func()
        await asyncio.sleep(delay)

def until00min():
    now = time.localtime()
    return (60 - now.tm_min) * 60 + now.tm_sec


@dataclass
class Cache:
    path: str
    score: dict[str, int] = field(default_factory=dict)


class Observer:

    def __init__(self, func, path='.', weight=1, pattern='%y%m%d%H'):
        self.func = func
        self.path = path
        self.weight = weight
        self.pattern = pattern
        self.cache = self.loadCache()

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
        window = self.func()
        if window not in self.cache.score:
            self.cache.score[window] = 0
        self.cache.score[window] += self.weight

    def commit(self):
        with open(self.cache.path, 'w') as file:
            file.write(yaml.dump(self.cache.score))

    async def observe(self):
        coros = (
            repeat(self.update, delay=1),
            repeat(self.commit, delay=10*60),
            repeat(self.reload, delay=60*60, wait=until00min())
        )
        await asyncio.gather(*coros)
