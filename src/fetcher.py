# -*- coding: utf-8 -*-
import requests
import re
from bs4 import BeautifulSoup
from .config import GAME_CONFIG

_BASE = "https://www.mizuhobank.co.jp/takarakuji/check/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.60 Safari/537.36",
    "Referer": "https://www.mizuhobank.co.jp/",
}

def _get_with_session(url: str) -> str:
    session = requests.Session()
    try:
        res = session.get(url, headers=_HEADERS, timeout=20)
        res.encoding = res.apparent_encoding
        if res.status_code == 200:
            return res.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""

def _parse_table_generic(html: str, game: str) -> list:
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    results = []
    pick = GAME_CONFIG[game]["pick"]
    is_numbers = "numbers" in game

    for table in soup.select("table.typeTK"):
        rows = table.select("tr")
        for r in rows:
            cols = [c.text.strip().replace("\xa0", " ") for c in r.select("th, td")]
            if len(cols) < 2: continue
            match = re.search(r"第?(\d+)回", cols[0])
            if not match: continue
            round_no = int(match.group(1))
            try:
                if is_numbers:
                    for col_text in cols[1:5]:
                        clean_text = re.sub(r"\D", "", col_text)
                        if len(clean_text) == pick:
                            nums = [int(d) for d in clean_text]
                            results.append({"round": round_no, "numbers": nums, "bonus": None})
                            break
                else:
                    nums = []
                    bonus = []
                    for col_text in cols[1:]:
                        clean_text = re.sub(r"\D", "", col_text)
                        if clean_text and len(clean_text) <= 2:
                            if len(nums) < pick: nums.append(int(clean_text))
                            else: bonus.append(int(clean_text))
                    if len(nums) == pick:
                        results.append({"round": round_no, "numbers": nums, "bonus": bonus if bonus else None})
            except: continue
    return results

def fetch_latest(game: str) -> list:
    """最新回のデータを取得する"""
    category = "numbers" if "numbers" in game else "loto"
    url = f"{_BASE}{category}/{game}/index.html"
    print(f"Fetching latest {game} from {url}...")
    html = _get_with_session(url)
    return _parse_table_generic(html, game)
