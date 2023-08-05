import os
import re
import yaml
from datetime import datetime


class Observer:

    def __init__(self, path='.'):
        self.base_path = path
        self.temp_path = path + '/temp'
        if not os.path.exists(self.temp_path):
            os.mkdir(self.temp_path)
        self.windows = set()
        self.points = dict()

    def local_update(self, windows, weight=10):
        for window in self.windows & windows:
            self.points[window] += weight
        self.windows = windows

    def cache_update(self):
        data = yaml.dump(self.points)
        date = datetime.strftime(datetime.now(), '%y%m%d%H%M')
        with open(f'{self.temp_path}/{date}.log') as file:
            file.write(data)
        self.points.clear()

    def final_update(self):
        pass
