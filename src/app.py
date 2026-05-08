# -*- coding: utf-8 -*-
import os
import sys
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# パス設定
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from src.config import GAME_CONFIG, ALL_GAMES
from src.storage import SQLiteManager
from src.analyzer import FlowAnalyzer
from src.fetcher import fetch_latest
from src.importer import CSVImporter

# テンプレートの場所を明示的に指定
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "gui", "templates"))
app = Flask(__name__, template_folder=template_dir)
CORS(app)

db = SQLiteManager()
analyzer = FlowAnalyzer()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["GET"])
def do_analyze():
    game = request.args.get("game", "loto6")
    history = db.load_game_data(game)
    result = analyzer.analyze(game, history)
    
    # 前回の実績も計算 (hit_count, hit_list) を取得
    hit_count, hit_list = analyzer.audit_last_round(game, history)
    result["last_hits"] = hit_count
    result["last_hit_list"] = hit_list
    
    # 解析の基点となった最新データ
    result["latest_draw"] = {
        "round": history[0]["round"],
        "date": history[0]["date"],
        "numbers": history[0]["numbers"]
    } if history else None
    
    return jsonify(result)

@app.route("/api/add_result", methods=["POST"])
def add_result():
    params = request.json
    game = params.get("game")
    round_no = int(params.get("round"))
    nums = [int(n) for n in params.get("numbers", "").split(",") if n.strip()]
    db.save_game_data(game, [{"round": round_no, "numbers": nums}])
    return jsonify({"status": "success"})

@app.route("/api/sync", methods=["GET"])
def sync_data():
    game = request.args.get("game", "loto6")
    new_data = fetch_latest(game)
    if new_data:
        db.save_game_data(game, new_data)
        return jsonify({"status": "success", "count": len(new_data)})
    return jsonify({"status": "error", "message": "取得失敗または更新なし"})

@app.route("/api/import_csv", methods=["GET"])
def import_csv():
    importer = CSVImporter()
    report = importer.import_all(root_dir)
    if report:
        return jsonify({"status": "success", "report": report})
    return jsonify({"status": "error", "message": "CSVファイルが見つからないか、インポートに失敗しました。"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
