import collections
import math
import itertools
from .config import GAME_CONFIG

class FlowAnalyzer:
    """川の流れ解析エンジン（RIVER-F 独自・マルチEMA × シナジー × 位置別解析版）"""
    
    def _calculate_ema(self, series, span):
        """EMA算出の共通関数"""
        if not series: return 0.0
        alpha = 2.0 / (span + 1)
        val = series[0]
        for v in series[1:]:
            val = alpha * v + (1 - alpha) * val
        return val

    def _get_synergy_score(self, n1, pool, synergy_map):
        """簡易シナジー：候補プール内の他の数字との過去の共起性を評価"""
        score = 0.0
        for n2 in pool:
            if n1 == n2: continue
            pair = tuple(sorted((n1, n2)))
            score += synergy_map.get(pair, 0)
        return score

    def analyze(self, game, history):
        if not history or len(history) < 30:
            return {"hot": [], "cold": [], "excluded": [], "message": "データが不足しています"}

        conf = GAME_CONFIG[game]
        pick = conf["pick"]
        max_val = conf["max_val"]
        is_numbers = "numbers" in game
        r_range = range(10) if is_numbers else range(1, max_val + 1)
        
        # 1. データの数値化
        # history[0]が最新なのでリバースして時系列(古い順)を作成
        time_series = {i: [1.0 if i in r["numbers"] else 0.0 for r in reversed(history[:50])] for i in r_range}
        
        # 2. マルチEMA収束解析 (短期 5 / 中期 15)
        momenta = {}
        for i in r_range:
            short_ema = self._calculate_ema(time_series[i], 5)
            mid_ema   = self._calculate_ema(time_series[i], 15)
            # 流速 (Velocity) 
            velocity = short_ema - mid_ema
            momenta[i] = short_ema + velocity # 未来予測値

        # 3. 簡易シナジーマトリックスの構築（直近50回からペア出現頻度を抽出）
        synergy_map = collections.Counter()
        for r in history[:50]:
            nums = sorted(r["numbers"])
            for pair in itertools.combinations(nums, 2):
                synergy_map[pair] += 1
        
        # 4. 空白期間 (Gap)
        gaps = {i: 999 for i in r_range}
        for i, r in enumerate(history):
            for n in r["numbers"]:
                if n in gaps and gaps[n] == 999: gaps[n] = i

        # 5. 位置別解析 (Numbers専用)
        pos_analysis = []
        if is_numbers:
            for p in range(pick):
                p_scores = {}
                for digit in range(10):
                    p_series = [1.0 if (len(r["numbers"]) > p and r["numbers"][p] == digit) else 0.0 for r in reversed(history[:40])]
                    p_ema = self._calculate_ema(p_series, 8)
                    p_scores[digit] = p_ema
                best_digits = sorted(range(10), key=lambda d: p_scores[d], reverse=True)[:3]
                pos_analysis.append({"pos": p, "best": best_digits})

        # 6. 総合スコアリング
        # 仮のHotプールを先に作り、シナジーで補正する
        initial_hot = sorted(r_range, key=lambda x: momenta[x], reverse=True)[:conf["hot_count"] * 2]
        
        final_scores = {}
        for i in r_range:
            score = momenta[i]
            # シナジー補正 (他の有力候補と出やすいか)
            if i in initial_hot:
                score += self._get_synergy_score(i, initial_hot, synergy_map) * 0.05
            
            # 長期欠損(Cold)補正
            if gaps[i] > (max_val / pick * 2.5):
                score += 0.15
            
            # スライド連鎖 (前回数字の隣)
            for prev in history[0]["numbers"]:
                if abs(i - prev) == 1:
                    score += 0.05
            
            final_scores[i] = score

        # 結果抽出
        hot = sorted(r_range, key=lambda x: final_scores[x], reverse=True)[:conf["hot_count"]]
        cold_pool = [i for i in r_range if i not in hot]
        cold = sorted(cold_pool, key=lambda x: gaps[x], reverse=True)[:conf["cold_count"]]
        # 除外推奨（前回当選番号の中から、今回の期待値が低い順に抽出）
        excluded_candidates = [n for n in history[0]["numbers"] if n in final_scores and n not in hot]
        excluded = sorted(excluded_candidates, key=lambda x: final_scores[x])[:conf["exclude_count"]]
        
        msg = f"RIVER-F v14.0: マルチEMA収束と{len(synergy_map)}組のペア相性を解析。{'位置別解析を適用済み。' if is_numbers else ''}"
        
        return {
            "hot": sorted(hot),
            "cold": sorted(cold),
            "excluded": sorted(excluded),
            "pos_analysis": pos_analysis,
            "message": msg
        }

    def audit_last_round(self, game, history):
        if len(history) < 2: return 0, []
        current_result = history[0]["numbers"]
        past_history = history[1:]
        analysis = self.analyze(game, past_history)
        hits = [n for n in current_result if n in analysis["hot"] or n in analysis["cold"]]
        return len(hits), hits
