# -*- coding: utf-8 -*-
import csv
import os
import re
import json
import sqlite3

# 同一ディレクトリのconfigをインポート
try:
    from src.config import DB_PATH, GAME_CONFIG
except ImportError:
    from config import DB_PATH, GAME_CONFIG

class CSVImporter:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_table(self, conn, game):
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{game}" (round INTEGER PRIMARY KEY, date TEXT, numbers TEXT, bonus TEXT)')

    def clean_numbers_val(self, val):
        match = re.search(r'(\d+)', val)
        if match:
            return match.group(1)
        return re.sub(r'\D', '', val)

    def import_all(self, base_dir="."):
        mapping = {
            "loto6": "ロト6.csv",
            "loto7": "ロト7.csv",
            "miniloto": "ミニロト.csv",
            "numbers3": "ナンバーズ3.csv",
            "numbers4": "ナンバーズ4.csv",
        }
        
        report = {}
        for game, filename in mapping.items():
            path = os.path.join(base_dir, filename)
            if not os.path.exists(path):
                print(f"Skipping {game}: {filename} not found.")
                continue
            
            print(f"Importing {game} from {filename}...")
            data_to_save = []
            
            # 日本語CSVによくある文字コードを試行
            encodings = ['utf-8-sig', 'shift_jis', 'cp932']
            success = False
            for enc in encodings:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        pick = GAME_CONFIG[game]["pick"]
                        is_numbers = "numbers" in game
                        
                        data_to_save = []
                        for row in reader:
                            if not row or len(row) < 3: continue
                            round_no = int(row[0])
                            date_str = row[1]
                            
                            if is_numbers:
                                num_str = self.clean_numbers_val(row[2])
                                nums = [int(d) for d in num_str]
                                bonus = None
                            else:
                                nums = [int(x) for x in row[2:2+pick]]
                                bonus_idx = 2 + pick
                                bonus = []
                                if game == "loto7":
                                    bonus = [int(row[bonus_idx]), int(row[bonus_idx+1])]
                                else:
                                    if bonus_idx < len(row) and row[bonus_idx]:
                                        bonus = [int(row[bonus_idx])]
                            
                            data_to_save.append({
                                "round": round_no,
                                "date": date_str,
                                "numbers": nums,
                                "bonus": bonus
                            })
                    success = True
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error during import {game} with {enc}: {e}")
                    break
            
            if success and data_to_save:
                self.save_to_db(game, data_to_save)
                report[game] = len(data_to_save)
                print(f"Successfully imported {len(data_to_save)} records for {game}.")
            elif not success:
                print(f"Failed to decode {filename} with any supported encoding.")
        return report

    def save_to_db(self, game, data):
        with self._connect() as conn:
            self._ensure_table(conn, game)
            for row in data:
                conn.execute(f'INSERT OR REPLACE INTO "{game}" (round, date, numbers, bonus) VALUES (?, ?, ?, ?)',
                    (row["round"], row.get("date"), json.dumps(row["numbers"]), json.dumps(row.get("bonus"))))

if __name__ == "__main__":
    import sys
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    
    importer = CSVImporter()
    importer.import_all(root)
