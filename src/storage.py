# -*- coding: utf-8 -*-
import sqlite3
import json
import os
from .config import DB_PATH, ALL_GAMES

class SQLiteManager:
    def __init__(self, db_path=DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_table(self, conn, game):
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{game}" (round INTEGER PRIMARY KEY, date TEXT, numbers TEXT, bonus TEXT)')

    def save_game_data(self, game, data):
        if not data: return
        with self._connect() as conn:
            self._ensure_table(conn, game)
            for row in data:
                conn.execute(f'INSERT OR REPLACE INTO "{game}" (round, date, numbers, bonus) VALUES (?, ?, ?, ?)',
                    (row["round"], row.get("date"), json.dumps(row["numbers"]), json.dumps(row.get("bonus"))))

    def load_game_data(self, game):
        with self._connect() as conn:
            self._ensure_table(conn, game)
            cur = conn.execute(f'SELECT round, date, numbers, bonus FROM "{game}" ORDER BY round DESC')
            rows = cur.fetchall()
        return [{"round": r[0], "date": r[1], "numbers": json.loads(r[2]), "bonus": json.loads(r[3]) if r[3] else None} for r in rows]

    def get_latest_round(self, game):
        data = self.load_game_data(game)
        return data[0] if data else None
