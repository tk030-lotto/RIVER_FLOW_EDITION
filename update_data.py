import os
import sys
import json
import re
import time
import requests
import io
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DATA_UPDATER")

# ロトライフのCSV URL定義
LOTTERY_CSV_URLS = {
    'loto6': 'https://loto-life.net/csv/loto6',
    'loto7': 'https://loto-life.net/csv/loto7',
    'miniloto':  'https://loto-life.net/csv/mini'
}

def clean_val(val):
    if not isinstance(val, str):
        return val
    s = val.strip()
    match = re.search(r'="(.+?)"', s)
    if match:
        return match.group(1)
    return s.strip('"')

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(clean_val)

def fetch_and_parse_csv(game_key, url):
    logger.info(f"Downloading CSV for {game_key} from {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            break
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            if attempt == max_retries:
                raise e
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
    csv_bytes = response.content
    decoded_text = None
    for enc in ('cp932', 'utf-8', 'utf-8-sig'):
        try:
            decoded_text = csv_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
            
    if not decoded_text:
        raise ValueError(f"Failed to decode CSV bytes for {game_key}")
        
    df = pd.read_csv(io.StringIO(decoded_text.strip()))
    df.columns = [clean_val(c) if isinstance(c, str) else c for c in df.columns]
    df = clean_data(df)
    
    parsed_history = []
    
    pick_counts = {
        'loto6': 6,
        'loto7': 7,
        'miniloto': 5
    }
    
    pick_count = pick_counts[game_key]
    
    for _, row in df.iterrows():
        try:
            round_no = int(row['開催回'])
            date_str = str(row['開催日']).strip()
            
            numbers = []
            for i in range(1, pick_count + 1):
                numbers.append(int(row[f'第{i}数字']))
            
            bonus = []
            if game_key == 'loto7':
                bonus = [int(row['ボーナス数字1']), int(row['ボーナス数字2'])]
            else:
                bonus = [int(row['ボーナス数字'])]
            
            parsed_history.append({
                "round": round_no,
                "date": date_str,
                "numbers": numbers,
                "bonus": bonus
            })
        except Exception:
            continue
            
    # 開催回降順でソート
    parsed_history.sort(key=lambda x: x['round'], reverse=True)
    return parsed_history

def main():
    target_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loto_data.js")
    
    all_data = {}
    success_count = 0
    
    for game_key, url in LOTTERY_CSV_URLS.items():
        try:
            history = fetch_and_parse_csv(game_key, url)
            if not history:
                logger.error(f"No parsed data for {game_key}")
                continue
            all_data[game_key] = history
            success_count += 1
        except Exception as e:
            logger.error(f"Error updating {game_key}: {e}")
            
    if success_count == len(LOTTERY_CSV_URLS):
        # loto_data.js を直接書き出し
        try:
            js_content = f"const LOTO_INIT_DATA = {json.dumps(all_data, ensure_ascii=False, indent=2)};\n"
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(js_content)
            logger.info(f"Successfully updated loto_data.js. Rounds: Loto6={len(all_data['loto6'])}, Loto7={len(all_data['loto7'])}, MiniLoto={len(all_data['miniloto'])}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error writing to loto_data.js: {e}")
            sys.exit(1)
    else:
        logger.warning(f"Some updates failed. Successful: {success_count}/{len(LOTTERY_CSV_URLS)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
