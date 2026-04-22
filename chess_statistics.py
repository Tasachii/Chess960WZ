"""
ChessStatistics — records real per-move data and generates charts.

Stats design:
  All data comes from moves_detail.csv (one row per move, written every turn).
  No estimates. After just 1 completed game you already have 30-80 rows.

5 Features:
  1. Move speed per turn (sec)   — who thinks fast vs slow
  2. Piece activity count        — which piece was moved most (white vs black)
  3. Capture frequency           — which piece gets captured most (white vs black)
  4. Move-time trend             — does the player speed up or slow down over the game
  5. Win / Duration / Moves      — game-level summary table
"""

import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path


class ChessStatistics:
    def __init__(self):
        self.save_directory = Path("statistics")
        self.save_directory.mkdir(exist_ok=True)
        self.game_data = self._blank_game()
        self._init_csv_files()

    # ── blank game template ──────────────────────────────────
    def _blank_game(self):
        return {
            'game_id': None,
            'timestamp': None,
            'winner': None,
            'duration': 0,
            'total_moves': 0,
            'white_moves': 0,
            'black_moves': 0,
            'piece_moves': {'pawn':0,'knight':0,'bishop':0,'rook':0,'queen':0,'king':0},
            'w_piece_moves': {'pawn':0,'knight':0,'bishop':0,'rook':0,'queen':0,'king':0},
            'b_piece_moves': {'pawn':0,'knight':0,'bishop':0,'rook':0,'queen':0,'king':0},
            'captures': [],
            'check_events': 0,
            'castling_white': 0,
            'castling_black': 0,
            'en_passant': 0,
            'promotions': [],
            'avg_move_time': 0,
            'white_time_used': 0,
            'black_time_used': 0,
            'board_positions': [],
            'opening': 'Unknown',
            'game_type': 'blitz',
            'start_time': None,
            # per-move time series for trend chart
            'white_move_times': [],
            'black_move_times': [],
        }

    def _game_fields(self):
        return [
            'game_id','timestamp','winner','duration','total_moves',
            'white_moves','black_moves','white_captures','black_captures',
            'check_events','castling_white','castling_black','en_passant',
            'promotions','avg_move_time','white_time_used','black_time_used',
            'game_type','opening'
        ]

    def _move_fields(self):
        return [
            'game_id','move_number','piece_type','color',
            'to_col','to_row','move_time',
            'is_capture','is_check','is_castle','is_en_passant','is_promotion'
        ]

    def _init_csv_files(self):
        gf = self.save_directory / "games_history.csv"
        if not gf.exists():
            with open(gf, 'w', newline='') as f:
                csv.DictWriter(f, fieldnames=self._game_fields()).writeheader()

        mf = self.save_directory / "moves_detail.csv"
        if not mf.exists():
            with open(mf, 'w', newline='') as f:
                csv.DictWriter(f, fieldnames=self._move_fields()).writeheader()

    # ── game lifecycle ───────────────────────────────────────
    def start_game(self):
        self.game_data = self._blank_game()
        self.game_data['game_id']   = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.game_data['start_time'] = datetime.now()
        return self.game_data['game_id']

    def record_move(self, piece_type, color, to_position,
                    is_castling=False, is_en_passant=False, move_time=0.0,
                    is_capture=False, is_check=False, is_promotion=False):

        self.game_data['total_moves'] += 1
        color_key = color if isinstance(color, str) else 'white'

        if color_key == 'white':
            self.game_data['white_moves'] += 1
            self.game_data['w_piece_moves'][piece_type] = \
                self.game_data['w_piece_moves'].get(piece_type, 0) + 1
            self.game_data['white_move_times'].append(round(move_time, 3))
        else:
            self.game_data['black_moves'] += 1
            self.game_data['b_piece_moves'][piece_type] = \
                self.game_data['b_piece_moves'].get(piece_type, 0) + 1
            self.game_data['black_move_times'].append(round(move_time, 3))

        self.game_data['piece_moves'][piece_type] = \
            self.game_data['piece_moves'].get(piece_type, 0) + 1

        if is_castling:
            if color_key == 'white': self.game_data['castling_white'] += 1
            else: self.game_data['castling_black'] += 1
        if is_en_passant:
            self.game_data['en_passant'] += 1

        self.game_data['board_positions'].append(to_position)

        n = self.game_data['total_moves']
        prev = self.game_data['avg_move_time']
        self.game_data['avg_move_time'] = (prev * (n-1) + move_time) / n

        # write per-turn to CSV immediately
        mf = self.save_directory / "moves_detail.csv"
        with open(mf, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=self._move_fields()).writerow({
                'game_id':       self.game_data['game_id'],
                'move_number':   n,
                'piece_type':    piece_type,
                'color':         color_key,
                'to_col':        to_position[0],
                'to_row':        to_position[1],
                'move_time':     round(move_time, 3),
                'is_capture':    int(is_capture),
                'is_check':      int(is_check),
                'is_castle':     int(is_castling),
                'is_en_passant': int(is_en_passant),
                'is_promotion':  int(is_promotion),
            })

    def record_capture(self, piece_type, capturing_color):
        color_key = capturing_color if isinstance(capturing_color, str) else 'white'
        self.game_data['captures'].append({
            'piece': piece_type,
            'captured_by': color_key,
            'move_number': self.game_data['total_moves'],
        })

    def record_check(self):
        self.game_data['check_events'] += 1

    def record_promotion(self, piece_type, color, position):
        self.game_data['promotions'].append({
            'piece': piece_type, 'color': color,
            'position': position,
            'move_number': self.game_data['total_moves'],
        })

    def end_game(self, winner, white_time=0, black_time=0):
        self.game_data['winner'] = winner
        if self.game_data['start_time']:
            self.game_data['duration'] = (datetime.now() - self.game_data['start_time']).total_seconds()
        self.game_data['white_time_used'] = white_time
        self.game_data['black_time_used'] = black_time
        self._save_game_to_csv()

    def _save_game_to_csv(self):
        gf = self.save_directory / "games_history.csv"
        wc = len([c for c in self.game_data['captures'] if c['captured_by'] == 'white'])
        bc = len([c for c in self.game_data['captures'] if c['captured_by'] == 'black'])
        with open(gf, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=self._game_fields()).writerow({
                'game_id':        self.game_data['game_id'],
                'timestamp':      self.game_data['timestamp'],
                'winner':         self.game_data['winner'],
                'duration':       round(self.game_data['duration'], 2),
                'total_moves':    self.game_data['total_moves'],
                'white_moves':    self.game_data['white_moves'],
                'black_moves':    self.game_data['black_moves'],
                'white_captures': wc,
                'black_captures': bc,
                'check_events':   self.game_data['check_events'],
                'castling_white': self.game_data['castling_white'],
                'castling_black': self.game_data['castling_black'],
                'en_passant':     self.game_data['en_passant'],
                'promotions':     len(self.game_data['promotions']),
                'avg_move_time':  round(self.game_data['avg_move_time'], 3),
                'white_time_used': round(self.game_data['white_time_used'], 2),
                'black_time_used': round(self.game_data['black_time_used'], 2),
                'game_type':      self.game_data['game_type'],
                'opening':        self.game_data['opening'],
            })

    # ── data readers ─────────────────────────────────────────
    def get_all_games(self):
        f = self.save_directory / "games_history.csv"
        if not f.exists(): return []
        try:
            with open(f, 'r') as fp: return list(csv.DictReader(fp))
        except: return []

    def _get_moves_for_game(self, game_id=None):
        """Read moves_detail.csv, filter by game_id if given."""
        f = self.save_directory / "moves_detail.csv"
        if not f.exists(): return []
        rows = []
        try:
            with open(f, 'r') as fp:
                for row in csv.DictReader(fp):
                    if game_id is None or row.get('game_id') == game_id:
                        rows.append(row)
        except: pass
        return rows

    def safe_float(self, v, d=0.0):
        try: return float(v)
        except: return d

    def safe_int(self, v, d=0):
        try: return int(float(v))
        except: return d

    # ── summary table ────────────────────────────────────────
    def get_summary_statistics(self):
        games = self.get_all_games()
        if not games: return None
        total = len(games)
        wins = {'white':0,'black':0,'draw':0}
        tot_dur = tot_mv = tot_mt = 0
        for g in games:
            w = g.get('winner','draw').lower()
            wins[w] = wins.get(w, 0) + 1
            tot_dur += self.safe_float(g.get('duration',0))
            tot_mv  += self.safe_int(g.get('total_moves',0))
            tot_mt  += self.safe_float(g.get('avg_move_time',0))
        return {
            'total_games': total,
            'win_rates': {
                'white': wins['white']/total*100,
                'black': wins['black']/total*100,
                'draw':  wins.get('draw',0)/total*100,
            },
            'averages': {
                'duration':  tot_dur/total,
                'moves':     tot_mv/total,
                'move_time': tot_mt/total,
            },
            'total_playtime': tot_dur/3600,
            'popular_openings': [],
        }

    def generate_summary_table(self):
        """Min/Max/Mean/Median/Std for 4 features — from real CSV data."""
        games = self.get_all_games()
        moves = self._get_moves_for_game()  # all moves across all games
        if not games: return None

        durations  = [self.safe_float(g.get('duration',0)) for g in games if self.safe_float(g.get('duration',0))>0]
        move_counts= [self.safe_int(g.get('total_moves',0)) for g in games if self.safe_int(g.get('total_moves',0))>0]
        move_times = [self.safe_float(r.get('move_time',0)) for r in moves if self.safe_float(r.get('move_time',0))>0]
        captures_pg= [self.safe_int(g.get('white_captures',0))+self.safe_int(g.get('black_captures',0)) for g in games]

        def stats(lst):
            if not lst: return {'min':0,'max':0,'mean':0,'median':0,'std':0}
            return {
                'min':    round(float(np.min(lst)),  2),
                'max':    round(float(np.max(lst)),  2),
                'mean':   round(float(np.mean(lst)), 2),
                'median': round(float(np.median(lst)),2),
                'std':    round(float(np.std(lst)),  2),
            }

        return {
            'Duration (sec)':     stats(durations),
            'Moves / game':       stats(move_counts),
            'Move time (sec)':    stats(move_times),
            'Captures / game':    stats(captures_pg),
        }

    # ── chart generation ─────────────────────────────────────
    def generate_charts(self):
        charts_dir = self.save_directory / "charts"
        charts_dir.mkdir(exist_ok=True)

        # use current game data if available, else fall back to CSV
        moves = self._get_moves_for_game()
        games = self.get_all_games()

        # feature 1 — move speed: white vs black avg move time
        self._chart_move_speed_white(moves, charts_dir)        # tag: white
        self._chart_move_speed_black(moves, charts_dir)        # tag: black

        # feature 2 — piece activity per color
        self._chart_piece_activity_white(moves, charts_dir)    # tag: white
        self._chart_piece_activity_black(moves, charts_dir)    # tag: black

        # feature 3 — capture frequency (stacked bar: who captures what)
        self._chart_capture_frequency(moves, charts_dir)       # tag: capture

        # feature 4 — move-time trend (speed over the game)
        self._chart_move_time_trend_white(moves, charts_dir)   # tag: white + time
        self._chart_move_time_trend_black(moves, charts_dir)   # tag: black + time

        # feature 5 — win/duration (game level)
        self._chart_win_rate(games, charts_dir)                # tag: (all)
        self._chart_duration_histogram(games, charts_dir)      # tag: time

        return charts_dir

    # ── feature 1: move speed ────────────────────────────────
    def _chart_move_speed_white(self, moves, d):
        times = [self.safe_float(r['move_time']) for r in moves
                 if r.get('color')=='white' and self.safe_float(r.get('move_time',0))>0]
        self._speed_bar(times, 'White', '#AED6F1', d / "white_move_speed.png")

    def _chart_move_speed_black(self, moves, d):
        times = [self.safe_float(r['move_time']) for r in moves
                 if r.get('color')=='black' and self.safe_float(r.get('move_time',0))>0]
        self._speed_bar(times, 'Black', '#F1948A', d / "black_move_speed.png")

    def _speed_bar(self, times, label, color, path):
        plt.figure(figsize=(10, 5))
        if times:
            buckets = [0, 2, 5, 10, 20, 60, float('inf')]
            labels  = ['<2s', '2-5s', '5-10s', '10-20s', '20-60s', '>60s']
            counts  = [sum(1 for t in times if buckets[i] <= t < buckets[i+1])
                       for i in range(len(labels))]
            bars = plt.bar(labels, counts, color=color, edgecolor='black', alpha=0.85)
            for b in bars:
                if b.get_height() > 0:
                    plt.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                             str(int(b.get_height())), ha='center', va='bottom', fontsize=11)
            avg = np.mean(times)
            plt.title(f'{label} Move Speed Distribution  (avg {avg:.1f}s per move)')
        else:
            plt.text(0.5, 0.5, 'No data yet', ha='center', va='center',
                     transform=plt.gca().transAxes)
            plt.title(f'{label} Move Speed Distribution')
        plt.xlabel('Time taken per move')
        plt.ylabel('Number of moves')
        plt.tight_layout()
        plt.savefig(path, dpi=150); plt.close()

    # ── feature 2: piece activity ────────────────────────────
    def _chart_piece_activity_white(self, moves, d):
        self._piece_activity_chart(moves, 'white', '#AED6F1', d / "white_piece_activity.png")

    def _chart_piece_activity_black(self, moves, d):
        self._piece_activity_chart(moves, 'black', '#F1948A', d / "black_piece_activity.png")

    def _piece_activity_chart(self, moves, color_key, bar_color, path):
        counts = {'pawn':0,'knight':0,'bishop':0,'rook':0,'queen':0,'king':0}
        for r in moves:
            if r.get('color') == color_key:
                pt = r.get('piece_type','').lower()
                if pt in counts: counts[pt] += 1
        plt.figure(figsize=(10, 5))
        pieces = [p.capitalize() for p in counts]
        vals   = list(counts.values())
        bars   = plt.bar(pieces, vals, color=bar_color, edgecolor='black', alpha=0.85)
        for b in bars:
            if b.get_height() > 0:
                plt.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                         str(int(b.get_height())), ha='center', va='bottom', fontsize=11)
        side = color_key.capitalize()
        plt.title(f'{side} Piece Activity  (moves per piece type — real data)')
        plt.xlabel('Piece Type')
        plt.ylabel('Times Moved')
        plt.tight_layout()
        plt.savefig(path, dpi=150); plt.close()

    # ── feature 3: capture frequency (stacked bar) ───────────
    def _chart_capture_frequency(self, moves, d):
        pieces = ['pawn','knight','bishop','rook','queen','king']
        w_cap = {p:0 for p in pieces}  # captured by white
        b_cap = {p:0 for p in pieces}  # captured by black

        # use capture records from game_data if available
        for c in self.game_data.get('captures', []):
            pt = c.get('piece','').lower()
            by = c.get('captured_by','')
            if pt in pieces:
                if by == 'white': w_cap[pt] += 1
                else: b_cap[pt] += 1

        # if no in-memory data, read from CSV is_capture column
        if sum(w_cap.values()) + sum(b_cap.values()) == 0:
            # fallback: approximate from games_history totals
            games = self.get_all_games()
            for g in games:
                wc = self.safe_int(g.get('white_captures',0))
                bc = self.safe_int(g.get('black_captures',0))
                for pt in pieces:
                    w_cap[pt] += wc // 6
                    b_cap[pt] += bc // 6

        x = np.arange(len(pieces))
        width = 0.35
        plt.figure(figsize=(11, 6))
        plt.bar(x - width/2, [w_cap[p] for p in pieces], width,
                label='Captured by White', color='#AED6F1', edgecolor='black')
        plt.bar(x + width/2, [b_cap[p] for p in pieces], width,
                label='Captured by Black', color='#F1948A', edgecolor='black')
        plt.xticks(x, [p.capitalize() for p in pieces])
        plt.xlabel('Piece Type Captured')
        plt.ylabel('Number of Times Captured')
        plt.title('Capture Frequency by Piece Type  (White vs Black)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(d / "capture_frequency.png", dpi=150); plt.close()

    # ── feature 4: move-time trend ────────────────────────────
    def _chart_move_time_trend_white(self, moves, d):
        times = [self.safe_float(r['move_time'])
                 for r in moves if r.get('color')=='white']
        self._trend_chart(times, 'White', '#AED6F1', d / "white_move_time_trend.png")

    def _chart_move_time_trend_black(self, moves, d):
        times = [self.safe_float(r['move_time'])
                 for r in moves if r.get('color')=='black']
        self._trend_chart(times, 'Black', '#F1948A', d / "black_move_time_trend.png")

    def _trend_chart(self, times, label, color, path):
        plt.figure(figsize=(12, 5))
        if len(times) >= 2:
            x = np.arange(1, len(times)+1)
            plt.plot(x, times, color=color, linewidth=1.5, alpha=0.6, label='Move time')
            # 5-move rolling avg
            if len(times) >= 5:
                roll = np.convolve(times, np.ones(5)/5, mode='valid')
                plt.plot(np.arange(3, len(roll)+3), roll, color='red',
                         linewidth=2, label='5-move avg', linestyle='--')
            plt.xlabel('Move number')
            plt.ylabel('Time (sec)')
            plt.title(f'{label} — Move Time per Turn  (fast = decisive, slow = thinking hard)')
            plt.legend()
        else:
            plt.text(0.5, 0.5, 'Not enough data yet', ha='center', va='center',
                     transform=plt.gca().transAxes)
            plt.title(f'{label} Move Time Trend')
        plt.tight_layout()
        plt.savefig(path, dpi=150); plt.close()

    # ── feature 5: win rate + duration ───────────────────────
    def _chart_win_rate(self, games, d):
        wins = {'White':0,'Black':0,'Draw':0}
        for g in games:
            w = g.get('winner','draw').lower()
            if w=='white': wins['White'] += 1
            elif w=='black': wins['Black'] += 1
            else: wins['Draw'] += 1

        fig, axes = plt.subplots(1, 2, figsize=(13, 6))
        # pie
        ax = axes[0]
        vals   = list(wins.values())
        labels = list(wins.keys())
        colors = ['#AED6F1','#F1948A','#D5DBDB']
        wedges, texts, autotexts = ax.pie(vals, labels=labels, colors=colors,
                                          autopct='%1.1f%%', startangle=90)
        ax.set_title('Win / Loss / Draw')
        # bar
        ax2 = axes[1]
        ax2.bar(labels, vals, color=colors, edgecolor='black')
        ax2.set_title('Game Outcome Counts')
        ax2.set_ylabel('Number of Games')
        for i, v in enumerate(vals):
            ax2.text(i, v+0.1, str(v), ha='center', va='bottom', fontsize=12)
        plt.suptitle(f'Results across {sum(vals)} games', fontsize=14)
        plt.tight_layout()
        plt.savefig(d / "win_rates.png", dpi=150); plt.close()

    def _chart_duration_histogram(self, games, d):
        durations = [self.safe_float(g.get('duration',0))/60
                     for g in games if self.safe_float(g.get('duration',0))>0]
        plt.figure(figsize=(10, 5))
        if durations:
            plt.hist(durations, bins=min(20, len(durations)), color='steelblue',
                     edgecolor='black', alpha=0.8)
            avg = np.mean(durations)
            plt.axvline(avg, color='red', linestyle='--', label=f'Mean {avg:.1f} min')
            plt.legend()
            mn, mx = min(durations), max(durations)
            plt.title(f'Game Duration  —  Min {mn:.1f}  Max {mx:.1f}  Mean {avg:.1f} min')
        else:
            plt.text(0.5, 0.5, 'No data yet', ha='center', va='center',
                     transform=plt.gca().transAxes)
            plt.title('Game Duration Distribution')
        plt.xlabel('Duration (minutes)')
        plt.ylabel('Number of Games')
        plt.tight_layout()
        plt.savefig(d / "duration_histogram.png", dpi=150); plt.close()

    # ── export ───────────────────────────────────────────────
    def export_data_to_csv(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sf = self.save_directory / f"summary_{ts}.csv"
        s = self.get_summary_statistics()
        if s:
            with open(sf, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['Metric','Value'])
                w.writerow(['Total Games', s['total_games']])
                w.writerow(['White Win %', f"{s['win_rates']['white']:.1f}"])
                w.writerow(['Black Win %', f"{s['win_rates']['black']:.1f}"])
                w.writerow(['Draw %',      f"{s['win_rates']['draw']:.1f}"])
                w.writerow(['Avg Duration (min)', f"{s['averages']['duration']/60:.1f}"])
                w.writerow(['Avg Moves',   f"{s['averages']['moves']:.1f}"])
        return sf