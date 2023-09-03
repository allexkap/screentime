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
        self.scheduling()

    def load_cache(self):
        path = f'{self.path}/{datetime.strftime(datetime.now(), self.pattern)}'
        points = dict()
        if os.path.exists(path):
            with open(path) as file:
                return yaml.load(file.read(), yaml.Loader)
        return {'path': path, 'points': points}

    def reopen(self):
        self.commit()
        self.cache = load_cache()

    def update(self):
        try:
            window = self.func():
        except Exception as ex:
            window = None
            print('ex')
        if window not in self.cache['points']:
            self.cache['points'][window] = 0
        self.cache['points'][window] += self.weight

    def commit(self):
        with open(self.cache['path'], 'w') as file:
            file.write(yaml.dump(self.cache['points']))

    def scheduling(self):
        schedule.every( 1).seconds.do(self.update)
        schedule.every(10).minutes.do(self.commit)
        schedule.every(  ).hour.at('00:00').do(self.reopen)

    async def run(self):
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
