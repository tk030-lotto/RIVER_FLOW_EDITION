# -*- coding: utf-8 -*-
import requests
import os

def download_file(url, filename):
    print(f"Downloading {url} ...")
    try:
        # ユーザーエージェントを模倣してアクセスを安定させる
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Successfully saved to {filename}")
        return True
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
        return False

def sync_all_data(base_dir="."):
    targets = [
        ("https://loto-life.net/csv/loto6", "ロト6.csv"),
        ("https://loto-life.net/csv/loto7", "ロト7.csv"),
        ("https://loto-life.net/csv/mini", "ミニロト.csv"),
        ("https://loto-life.net/public/csv/numbers3", "ナンバーズ3.csv"),
        ("https://loto-life.net/public/csv/numbers4", "ナンバーズ4.csv"),
        ("https://loto-life.net/csv/bingo5", "ビンゴ5.csv"),
        ("https://r7-yosou.hippy.jp/T-data%20.xls", "T-data .xls")
    ]
    
    results = []
    for url, filename in targets:
        dest_path = os.path.join(base_dir, filename)
        success = download_file(url, dest_path)
        results.append((filename, success))
    
    return results

if __name__ == "__main__":
    print("--- RIVER FLOW EDITION: Data Sync Start ---")
    # プロジェクトルートに保存する想定
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sync_all_data(root)
    print("--- Sync Complete ---")
