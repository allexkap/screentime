import os
import yaml


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
        # with open(self.temp_path) as file:
        #     file.write(data)
        self.points.clear()

    def final_update(self):
        pass
