import os
import time
import yaml
import asyncio


async def wait(delay, coro):
    await asyncio.sleep(delay)
    await coro

async def repeat(func, delay):
    while True:
        func()
        await asyncio.sleep(delay)


class Observer:

    def __init__(self, func, path='.', weight=1, pattern='%y%m%d%H'):
        self.func = func
        self.path = path
        self.weight = weight
        self.pattern = pattern
        self.cache = self.load_cache()

    def load_cache(self):
        path = f'{self.path}/{time.strftime(self.pattern, time.localtime())}'
        if os.path.exists(path):
            with open(path) as file:
                return yaml.load(file.read(), yaml.Loader)
        return {'path': path, 'points': dict()}

    def reload(self):
        self.commit()
        self.cache = load_cache()

    def update(self):
        window = self.func()
        if window not in self.cache['points']:
            self.cache['points'][window] = 0
        self.cache['points'][window] += self.weight

    def commit(self):
        with open(self.cache['path'], 'w') as file:
            file.write(yaml.dump(self.cache['points']))

    async def observe(self):
        tasks = (
            repeat(self.update, delay=1),
            repeat(self.commit, delay=10*60),
            repeat(self.reload, delay=60*60, wait=(60-r.tm_min)*60+r.tm_sec)
        )
