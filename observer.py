import os
import yaml
import schedule
import asyncio
from datetime import datetime


class Observer:

    def __init__(self, func, path='.', weight=1, pattern='%y%m%d%H'):
        self.func = func
        self.path = path
        self.weight = weight
        self.pattern = pattern
        self.cache = self.load_cache()

    def load_cache(self):
        path = f'{self.path}/{datetime.strftime(datetime.now(), self.pattern)}'
        if os.path.exists(path):
            with open(path) as file:
                return yaml.load(file.read(), yaml.Loader)
        return {'path': path, 'points': dict()}

    def reload_cache(self):
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
        schedule.clear()
        schedule.every( 1).seconds.do(self.update)
        schedule.every(10).minutes.do(self.commit)
        schedule.every().hour.at('00:00').do(self.reload_cache)
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
