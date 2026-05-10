import csv
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path


class ChessStatistics:
    def __init__(self):
        self.save_directory = Path("statistics")
        self.save_directory.mkdir(exist_ok=True)
        self.charts_dir = self.save_directory / "charts"
        self.charts_dir.mkdir(exist_ok=True)

        self.game_data = self._blank_game()
        self.moves_csv = self.save_directory / "moves_detail.csv"
        self.games_csv = self.save_directory / "games_history.csv"
        self._init_csv_files()

    def _blank_game(self):
        return {
            'game_id': None,
            'timestamp': None,
            'winner': None,
            'duration': 0,
            'total_moves': 0,
            'white_moves': 0,
            'black_moves': 0,
            'white_captures': 0,
            'black_captures': 0,
            'check_events': 0,
            'white_time_used': 0,
            'black_time_used': 0,
            'game_type': 'unknown'
        }

    def _init_csv_files(self):
        if not self.games_csv.exists():
            with open(self.games_csv, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow([
                    'game_id', 'timestamp', 'winner', 'duration', 'total_moves',
                    'white_moves', 'black_moves', 'white_captures', 'black_captures',
                    'check_events', 'white_time_used', 'black_time_used', 'game_type'
                ])

        if not self.moves_csv.exists():
            with open(self.moves_csv, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow([
                    'game_id', 'move_number', 'piece_type', 'color',
                    'to_col', 'to_row', 'move_time', 'is_capture',
                    'captured_piece', 'is_check', 'is_castle', 'is_promotion'
                ])

    def start_game(self):
        ts = datetime.now()
        self.game_data = self._blank_game()
        self.game_data['game_id'] = ts.strftime("%Y%m%d_%H%M%S")
        self.game_data['timestamp'] = ts.strftime("%Y-%m-%d %H:%M:%S")

    def record_move(self, piece_type, color, to_pos, move_time=0.0, is_capture=False, captured_piece='none',
                    is_check=False, is_castle=False, is_promotion=False):
        self.game_data['total_moves'] += 1
        if color == 'white':
            self.game_data['white_moves'] += 1
            if is_capture: self.game_data['white_captures'] += 1
        else:
            self.game_data['black_moves'] += 1
            if is_capture: self.game_data['black_captures'] += 1

        if is_check:
            self.game_data['check_events'] += 1

        with open(self.moves_csv, 'a', newline='') as f:
            w = csv.writer(f)
            w.writerow([
                self.game_data['game_id'],
                self.game_data['total_moves'],
                piece_type,
                color,
                to_pos[0],
                to_pos[1],
                round(move_time, 3),
                1 if is_capture else 0,
                captured_piece,
                1 if is_check else 0,
                1 if is_castle else 0,
                1 if is_promotion else 0
            ])

    def end_game(self, winner, white_time_used, black_time_used):
        self.game_data['winner'] = winner
        self.game_data['white_time_used'] = round(white_time_used, 2)
        self.game_data['black_time_used'] = round(black_time_used, 2)
        self.game_data['duration'] = round(white_time_used + black_time_used, 2)

        with open(self.games_csv, 'a', newline='') as f:
            w = csv.writer(f)
            w.writerow([
                self.game_data['game_id'], self.game_data['timestamp'],
                self.game_data['winner'], self.game_data['duration'],
                self.game_data['total_moves'], self.game_data['white_moves'],
                self.game_data['black_moves'], self.game_data['white_captures'],
                self.game_data['black_captures'], self.game_data['check_events'],
                self.game_data['white_time_used'], self.game_data['black_time_used'],
                self.game_data['game_type']
            ])

    def generate_dynamic_chart(self, metric, color_filter='all'):
        move_metrics = ['dependency', 'hesitation', 'think_time', 'lethality']
        game_metrics = ['win_rate', 'duration_dist', 'move_trend']

        plt.figure(figsize=(8, 5))
        plt.style.use('dark_background')

        if metric in move_metrics:
            if not self.moves_csv.exists():
                return self._generate_empty_chart("No move data available")
            df = pd.read_csv(self.moves_csv)
            if df.empty:
                return self._generate_empty_chart("No move data available")

            if color_filter != 'all':
                df = df[df['color'] == color_filter]
                if df.empty:
                    return self._generate_empty_chart(f"No data for {color_filter}")

            if metric == 'dependency':
                piece_counts = df['piece_type'].value_counts()

                # แยกการตั้งค่า Text ด้านนอก และ % ด้านใน
                patches, texts, autotexts = plt.pie(
                    piece_counts,
                    labels=piece_counts.index,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=plt.cm.Pastel1.colors
                )

                # Label ด้านนอกสีขาว
                for text in texts:
                    text.set_color('white')
                    text.set_fontsize(12)
                # % ด้านในสีดำหนา
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_weight('bold')
                    autotext.set_fontsize(11)

                plt.title(f"Piece Dependency ({color_filter.upper()})", color='white')

            elif metric == 'hesitation':
                captures = df[df['is_capture'] == 1]
                if captures.empty: return self._generate_empty_chart("No captures found")
                avg_time = captures.groupby('piece_type')['move_time'].mean().sort_values()
                avg_time.plot(kind='bar', color='salmon')
                plt.title(f"Capture Hesitation ({color_filter.upper()})", color='white')
                plt.ylabel('Avg Time Before Attack (sec)', color='white')
                plt.xticks(rotation=45, color='white')

            elif metric == 'think_time':
                bins = [0, 10, 30, 1000]
                labels = ['Opening (1-10)', 'Middlegame (11-30)', 'Endgame (31+)']
                df['phase'] = pd.cut(df['move_number'], bins=bins, labels=labels, right=True)
                phase_time = df.groupby('phase', observed=False)['move_time'].mean().dropna()
                if phase_time.empty: return self._generate_empty_chart("Not enough data")
                phase_time.plot(kind='line', marker='o', color='cyan', linewidth=2)
                plt.title(f"Think Time by Phase ({color_filter.upper()})", color='white')
                plt.ylabel('Avg Think Time (sec)', color='white')
                plt.ylim(bottom=0)

            elif metric == 'lethality':
                captures = df[df['is_capture'] == 1]
                if captures.empty: return self._generate_empty_chart("No captures found")
                matrix = pd.crosstab(captures['piece_type'], captures['captured_piece'])
                matrix.plot(kind='bar', stacked=True, colormap='viridis', ax=plt.gca())
                plt.title(f"Lethality Matrix ({color_filter.upper()})", color='white')
                plt.xlabel('Attacker', color='white')
                plt.ylabel('Kills', color='white')
                plt.legend(title='Target', bbox_to_anchor=(1.05, 1), loc='upper left')

        elif metric in game_metrics:
            if not self.games_csv.exists():
                return self._generate_empty_chart("No game data available")
            df = pd.read_csv(self.games_csv)
            if df.empty:
                return self._generate_empty_chart("No game data available")

            if metric == 'win_rate':
                wins = df['winner'].value_counts()
                colors_map = {'white': '#F5F5DC', 'black': '#FFD700', 'draw': '#B0C4DE'}
                pie_colors = [colors_map.get(w, '#aaaaaa') for w in wins.index]

                # แยกการตั้งค่า Text ด้านนอก และ % ด้านใน
                patches, texts, autotexts = plt.pie(
                    wins,
                    labels=wins.index,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=pie_colors
                )

                # Label ด้านนอกสีขาว
                for text in texts:
                    text.set_color('white')
                    text.set_fontsize(12)
                # % ด้านในสีดำหนา
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_weight('bold')
                    autotext.set_fontsize(12)

                plt.title("Overall Win Rates", color='white')

            elif metric == 'duration_dist':
                df['duration_min'] = df['duration'] / 60
                df['duration_min'].plot.hist(bins=15, color='purple', alpha=0.7)
                plt.title("Game Duration Distribution", color='white')
                plt.xlabel("Duration (minutes)", color='white')

            elif metric == 'move_trend':
                df['total_moves'].plot(kind='line', marker='.', color='orange')
                plt.title("Move Count Trend Across Games", color='white')
                plt.xlabel("Game Sequence", color='white')
                plt.ylabel("Total Half-Moves", color='white')

        out_path = self.charts_dir / "temp_chart.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=120, bbox_inches='tight')
        plt.close()
        return out_path

    def _generate_empty_chart(self, message):
        plt.figure(figsize=(8, 5))
        plt.style.use('dark_background')
        plt.text(0.5, 0.5, message, ha='center', va='center', fontsize=16, color='white')
        plt.axis('off')
        out_path = self.charts_dir / "temp_chart.png"
        plt.savefig(out_path, dpi=120)
        plt.close()
        return out_path

    def get_all_games(self):
        games = []
        if self.games_csv.exists():
            with open(self.games_csv, 'r') as f:
                r = csv.DictReader(f)
                for row in r: games.append(row)
        return games

    def get_summary_statistics(self):
        games = self.get_all_games()
        if not games: return None
        white_wins = sum(1 for g in games if g['winner'] == 'white')
        black_wins = sum(1 for g in games if g['winner'] == 'black')
        draws = sum(1 for g in games if g['winner'] == 'draw')
        total = len(games)
        return {
            'total_games': total,
            'win_rates': {
                'white': (white_wins / total) * 100,
                'black': (black_wins / total) * 100,
                'draw': (draws / total) * 100
            },
            'averages': {
                'duration': sum(float(g['duration']) for g in games) / total,
                'moves': sum(int(g['total_moves']) for g in games) / total
            },
            'total_playtime': sum(float(g['duration']) for g in games) / 3600
        }

    def generate_summary_table(self):
        if not self.games_csv.exists(): return None
        df = pd.read_csv(self.games_csv)
        if df.empty: return None
        summary = {}
        for col in ['duration', 'total_moves', 'white_time_used', 'black_time_used']:
            summary[col] = {
                'min': df[col].min(),
                'max': df[col].max(),
                'mean': df[col].mean(),
                'median': df[col].median(),
                'std': df[col].std() if len(df) > 1 else 0.0
            }
        return summary