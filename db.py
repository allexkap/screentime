import sqlite3
from datetime import datetime


class Cache:
    def __init__(self, data: list[tuple[int, str, int]] = []) -> None:
        timestamp: int | None = None
        cache: dict[str, int] = {}
        for entry in data:
            if timestamp is None:
                timestamp = entry[0]
            elif timestamp != entry[0]:
                raise ValueError('timestamps are not the same')
            if entry[1] in cache:
                raise ValueError('apps collision detected')
            cache[entry[1]] = entry[2]
        else:
            timestamp = int(datetime.now().timestamp()) // 3600 * 3600
        self.timestamp = timestamp
        self._cache = cache

    def __iter__(self):
        return self._cache.__iter__()

    def __getitem__(self, key) -> int:
        return self._cache.__getitem__(key)

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
    _select_all_by_timestamp_cmd = 'select * from activity where timestamp = ?'
    _select_all_by_app_cmd = 'select * from activity where app = ?'

    def __init__(self, path: str) -> None:
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()
        self.cur.execute(self._create_table_cmd)
        self.con.commit()
        self._update_cache()

    def _update_cache(self) -> None:
        timestamp = int(datetime.now().timestamp()) // 3600 * 3600
        data = self.cur.execute(
            self._select_all_by_timestamp_cmd, (timestamp,)
        ).fetchall()
        self.cache = Cache(data)

    def _validate_cache(self) -> None:
        timestamp = int(datetime.now().timestamp()) // 3600 * 3600
        if timestamp != self.cache.timestamp:
            self.commit()
            self._update_cache()

    def update(self, app: str, score: int) -> None:
        if app not in self.cache:
            self.cache[app] = 0
        self.cache[app] += score

    def commit(self) -> None:
        if self.cache is None:
            return
        with self.con:
            for entry in self.cache.export():
                self.cur.execute(self._update_row_cmd, entry)

    def __del__(self) -> None:
        self.commit()
        self.con.close()
