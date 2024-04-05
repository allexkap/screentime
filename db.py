import sqlite3
from datetime import datetime


class Cache:
    def __init__(self, timestamp: int, data: list[tuple[str, int]] = []) -> None:
        self.timestamp = timestamp
        self._cache: dict[str, int] = {}
        for entry in data:
            if entry[0] in self._cache:
                raise ValueError('apps collision detected')
            self._cache[entry[0]] = entry[1]

    def __getitem__(self, key) -> int:
        return self._cache.get(key, 0)

    def __setitem__(self, key, value) -> None:
        return self._cache.__setitem__(key, value)

    def export(self) -> list[tuple[int, str, int]]:
        return [(self.timestamp, app, self._cache[app]) for app in self._cache]


class Activity:

    _create_table_cmd = '''
        create table if not exists activity (
            timestamp integer not null,
            app text not null,
            seconds integer not null,
            primary key(timestamp, app)
        )
    '''
    _update_row_cmd = 'insert or replace into activity values (?, ?, ?)'
    _select_all_by_ts_cmd = 'select app, seconds from activity where timestamp = ?'
    _select_all_by_app_cmd = 'select * from activity where app = ?'

    def __init__(self, path: str) -> None:
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()
        self.cur.execute(self._create_table_cmd)
        self.con.commit()
        self._validate_cache(init=True)

    def _validate_cache(self, init: bool = False) -> None:
        timestamp = int(datetime.now().timestamp()) // 3600 * 3600
        if not init:
            if timestamp == self.cache.timestamp:
                return
            self.commit()
        data = self.cur.execute(self._select_all_by_ts_cmd, (timestamp,)).fetchall()
        self.cache = Cache(timestamp, data)

    def update(self, app: str, score: int) -> None:
        self._validate_cache()
        self.cache[app] += score

    def commit(self) -> None:
        with self.con:
            for entry in self.cache.export():
                self.cur.execute(self._update_row_cmd, entry)

    def __del__(self) -> None:
        self.commit()
        self.con.close()
