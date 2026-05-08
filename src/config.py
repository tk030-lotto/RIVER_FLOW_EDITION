# -*- coding: utf-8 -*-
"""
RIVER-F River Flow Edition: Core Config
"""
import os

GAME_CONFIG = {
    "loto6":    {"full_name": "LOTO 6",    "max_val": 43, "pick": 6, "hot_count": 8, "cold_count": 4, "exclude_count": 5},
    "loto7":    {"full_name": "LOTO 7",    "max_val": 37, "pick": 7, "hot_count": 9, "cold_count": 4, "exclude_count": 5},
    "miniloto": {"full_name": "MINI LOTO", "max_val": 31, "pick": 5, "hot_count": 7, "cold_count": 3, "exclude_count": 3},
    "numbers3": {"full_name": "NUMBERS 3", "max_val": 9,  "pick": 3, "hot_count": 3, "cold_count": 2, "exclude_count": 1},
    "numbers4": {"full_name": "NUMBERS 4", "max_val": 9,  "pick": 4, "hot_count": 3, "cold_count": 2, "exclude_count": 1},
}
ALL_GAMES = list(GAME_CONFIG.keys())
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "lottery.db"))
