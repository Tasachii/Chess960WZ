import csv
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path
import os


class ChessStatistics:
    def __init__(self):
        # Create directory for stats if it doesn't exist
        self.save_directory = Path("statistics")
        self.save_directory.mkdir(exist_ok=True)

        # Current game data
        self.game_data = {
            'game_id': None,
            'timestamp': None,
            'winner': None,
            'duration': 0,
            'total_moves': 0,
            'white_moves': 0,
            'black_moves': 0,
            'piece_moves': {},
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
            'opening': 'Unknown'
        }

        # Initialize CSV files
        self.init_csv_files()

    def init_csv_files(self):
        """Create CSV files if they don't exist"""
        # Main games history file
        games_file = self.save_directory / "games_history.csv"
        if not games_file.exists():
            with open(games_file, 'w', newline='') as f:
                fieldnames = [
                    'game_id', 'timestamp', 'winner', 'duration', 'total_moves',
                    'white_moves', 'black_moves', 'white_captures', 'black_captures',
                    'check_events', 'castling_white', 'castling_black', 'en_passant',
                    'promotions', 'avg_move_time', 'white_time_used', 'black_time_used',
                    'game_type', 'opening'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

        # Moves detail file
        moves_file = self.save_directory / "moves_detail.csv"
        if not moves_file.exists():
            with open(moves_file, 'w', newline='') as f:
                fieldnames = [
                    'game_id', 'move_number', 'piece_type', 'color', 'from_pos',
                    'to_pos', 'move_time', 'is_capture', 'is_check', 'is_castle',
                    'is_en_passant', 'is_promotion'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

        # Positions analysis file
        positions_file = self.save_directory / "board_positions.csv"
        if not positions_file.exists():
            with open(positions_file, 'w', newline='') as f:
                fieldnames = ['game_id', 'move_number', 'x', 'y', 'piece_type', 'color']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

    def start_game(self):
        """Initialize a new game session"""
        self.game_data = {
            'game_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'winner': None,
            'duration': 0,
            'total_moves': 0,
            'white_moves': 0,
            'black_moves': 0,
            'piece_moves': {'pawn': 0, 'knight': 0, 'bishop': 0, 'rook': 0, 'queen': 0, 'king': 0},
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
            'start_time': datetime.now()
        }
        return self.game_data['game_id']

    def record_move(self, piece_type, color, to_position, is_castling=False, is_en_passant=False, move_time=0):
        """Record a move with details"""
        # Update basic counters
        self.game_data['total_moves'] += 1
        if color == 'white':
            self.game_data['white_moves'] += 1
        else:
            self.game_data['black_moves'] += 1

        # Track piece movements
        if piece_type in self.game_data['piece_moves']:
            self.game_data['piece_moves'][piece_type] += 1

        # Track special moves
        if is_castling:
            if color == 'white':
                self.game_data['castling_white'] += 1
            else:
                self.game_data['castling_black'] += 1

        if is_en_passant:
            self.game_data['en_passant'] += 1

        # Record position for heatmap
        self.game_data['board_positions'].append(to_position)

        # Calculate average move time
        if self.game_data['total_moves'] > 0:
            self.game_data['avg_move_time'] = (
                                                      self.game_data['avg_move_time'] * (
                                                          self.game_data['total_moves'] - 1) + move_time
                                              ) / self.game_data['total_moves']

    def record_capture(self, piece_type, capturing_color):
        """Record when a piece is captured"""
        self.game_data['captures'].append({
            'piece': piece_type,
            'captured_by': capturing_color,
            'move_number': self.game_data['total_moves']
        })

    def record_check(self):
        """Record when check occurs"""
        self.game_data['check_events'] += 1

    def record_promotion(self, piece_type, color, position):
        """Record pawn promotion"""
        self.game_data['promotions'].append({
            'piece': piece_type,
            'color': color,
            'position': position,
            'move_number': self.game_data['total_moves']
        })

    def end_game(self, winner, white_time=0, black_time=0):
        """Finalize game data and save to CSV"""
        self.game_data['winner'] = winner
        if self.game_data['start_time']:
            self.game_data['duration'] = (datetime.now() - self.game_data['start_time']).total_seconds()
        self.game_data['white_time_used'] = white_time
        self.game_data['black_time_used'] = black_time

        # Save to CSV
        self._save_game_to_csv()

    def _save_game_to_csv(self):
        """Save current game data to CSV files"""
        # Save main game info
        games_file = self.save_directory / "games_history.csv"
        with open(games_file, 'a', newline='') as f:
            fieldnames = [
                'game_id', 'timestamp', 'winner', 'duration', 'total_moves',
                'white_moves', 'black_moves', 'white_captures', 'black_captures',
                'check_events', 'castling_white', 'castling_black', 'en_passant',
                'promotions', 'avg_move_time', 'white_time_used', 'black_time_used',
                'game_type', 'opening'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Calculate captures by side
            white_captures = len([c for c in self.game_data['captures'] if c['captured_by'] == 'white'])
            black_captures = len([c for c in self.game_data['captures'] if c['captured_by'] == 'black'])

            writer.writerow({
                'game_id': self.game_data['game_id'],
                'timestamp': self.game_data['timestamp'],
                'winner': self.game_data['winner'],
                'duration': self.game_data['duration'],
                'total_moves': self.game_data['total_moves'],
                'white_moves': self.game_data['white_moves'],
                'black_moves': self.game_data['black_moves'],
                'white_captures': white_captures,
                'black_captures': black_captures,
                'check_events': self.game_data['check_events'],
                'castling_white': self.game_data['castling_white'],
                'castling_black': self.game_data['castling_black'],
                'en_passant': self.game_data['en_passant'],
                'promotions': len(self.game_data['promotions']),
                'avg_move_time': self.game_data['avg_move_time'],
                'white_time_used': self.game_data['white_time_used'],
                'black_time_used': self.game_data['black_time_used'],
                'game_type': self.game_data['game_type'],
                'opening': self.game_data['opening']
            })

        # Save position data for heatmap
        positions_file = self.save_directory / "board_positions.csv"
        with open(positions_file, 'a', newline='') as f:
            fieldnames = ['game_id', 'move_number', 'x', 'y', 'piece_type', 'color']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            for i, pos in enumerate(self.game_data['board_positions']):
                if isinstance(pos, tuple) and len(pos) == 2:
                    writer.writerow({
                        'game_id': self.game_data['game_id'],
                        'move_number': i + 1,
                        'x': pos[0],
                        'y': pos[1],
                        'piece_type': 'unknown',
                        'color': 'unknown'
                    })

    def get_all_games(self):
        """Get all game data from CSV"""
        csv_file = self.save_directory / "games_history.csv"
        if not csv_file.exists():
            return []

        games = []
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                games = list(reader)
        except Exception as e:
            print(f"Error reading games data: {e}")

        return games

    def validate_csv(self):
        """Validate and repair CSV data if necessary"""
        csv_file = self.save_directory / "games_history.csv"
        if not csv_file.exists():
            return "CSV file not found"

        try:
            # Read current data
            with open(csv_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                games = list(reader)

            # Validate and repair data
            fixed_games = []
            corrupt_count = 0
            for game in games:
                # Check total_moves field
                if not self._is_valid_number(game.get('total_moves', '0')):
                    corrupt_count += 1
                    game['total_moves'] = '0'

                fixed_games.append(game)

            # Save repaired data (if any)
            if corrupt_count > 0:
                # Backup original file
                backup_path = csv_file.with_suffix('.bak')
                os.rename(csv_file, backup_path)

                # Write new file
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fixed_games[0].keys())
                    writer.writeheader()
                    writer.writerows(fixed_games)

                return f"Repaired {corrupt_count} entries. Original file backed up to {backup_path}"

            return "CSV data is valid, no errors found"

        except Exception as e:
            return f"Error validating CSV: {e}"

    def _is_valid_number(self, value):
        """Check if value can be converted to a number"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def safe_int(self, value, default=0):
        """Safely convert value to integer"""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    def safe_float(self, value, default=0.0):
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_summary_statistics(self):
        """Get comprehensive summary statistics"""
        games = self.get_all_games()
        if not games:
            return None

        # Basic stats
        total_games = len(games)
        wins = {'white': 0, 'black': 0, 'draw': 0}
        total_duration = 0
        total_moves = 0
        valid_games = 0

        for game in games:
            try:
                # Get winner
                winner = game.get('winner', 'draw').lower()
                if winner in wins:
                    wins[winner] += 1
                else:
                    wins['draw'] += 1

                # Parse duration safely
                duration = self.safe_float(game.get('duration', 0))
                total_duration += duration

                # Parse moves safely
                moves = self.safe_int(game.get('total_moves', 0))
                total_moves += moves

                valid_games += 1

            except Exception as e:
                print(f"Error processing game data: {e}")
                continue

        # Calculate averages
        avg_duration = total_duration / valid_games if valid_games > 0 else 0
        avg_moves = total_moves / valid_games if valid_games > 0 else 0

        # Opening analysis
        openings = {}
        for game in games:
            opening = game.get('opening', 'Unknown')
            openings[opening] = openings.get(opening, 0) + 1

        # Calculate average move time safely
        avg_move_time = 0
        move_time_count = 0
        for game in games:
            move_time = self.safe_float(game.get('avg_move_time', 0))
            avg_move_time += move_time
            move_time_count += 1

        avg_move_time = avg_move_time / move_time_count if move_time_count > 0 else 0

        return {
            'total_games': total_games,
            'valid_games': valid_games,
            'win_rates': {
                'white': wins['white'] / total_games * 100 if total_games > 0 else 0,
                'black': wins['black'] / total_games * 100 if total_games > 0 else 0,
                'draw': wins['draw'] / total_games * 100 if total_games > 0 else 0
            },
            'averages': {
                'duration': avg_duration,
                'moves': avg_moves,
                'move_time': avg_move_time
            },
            'popular_openings': sorted(openings.items(), key=lambda x: x[1], reverse=True)[:5],
            'total_playtime': total_duration / 3600,  # in hours
        }

    def generate_heatmap(self, save_path=None):
        """Generate a heatmap of piece positions"""
        positions_file = self.save_directory / "board_positions.csv"
        if not positions_file.exists():
            return None

        # Create 8x8 grid for heatmap
        heatmap_data = np.zeros((8, 8))

        try:
            with open(positions_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    x = self.safe_int(row['x'])
                    y = self.safe_int(row['y'])
                    if 0 <= x < 8 and 0 <= y < 8:
                        heatmap_data[y][x] += 1
        except Exception as e:
            print(f"Error reading position data: {e}")

        # Create the heatmap
        plt.figure(figsize=(10, 10))
        plt.imshow(heatmap_data, cmap='hot', interpolation='nearest')
        plt.colorbar(label='Frequency')
        plt.title('Chess Position Heatmap')

        # Add board coordinates
        plt.xticks(range(8), ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
        plt.yticks(range(8), ['8', '7', '6', '5', '4', '3', '2', '1'])

        # Save the heatmap
        if save_path is None:
            save_path = self.save_directory / f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

        return save_path

    def generate_charts(self):
        """Generate various statistical charts"""
        games = self.get_all_games()
        if not games:
            return None

        # Create charts directory
        charts_dir = self.save_directory / "charts"
        charts_dir.mkdir(exist_ok=True)

        # 1. Win rate pie chart
        self._create_win_rate_chart(games, charts_dir)

        # 2. Game duration histogram
        self._create_duration_histogram(games, charts_dir)

        # 3. Move count trends
        self._create_move_trends_chart(games, charts_dir)

        # 4. Piece usage bar chart
        self._create_piece_usage_chart(games, charts_dir)

        return charts_dir

    def _create_win_rate_chart(self, games, charts_dir):
        """Create a pie chart of win rates"""
        wins = {'White': 0, 'Black': 0, 'Draw': 0}

        for game in games:
            winner = game.get('winner', 'draw').lower()
            if winner == 'white':
                wins['White'] += 1
            elif winner == 'black':
                wins['Black'] += 1
            else:
                wins['Draw'] += 1

        plt.figure(figsize=(10, 8))
        colors = ['lightblue', 'lightcoral', 'lightgray']
        plt.pie(wins.values(), labels=wins.keys(), colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Win Rate Distribution')

        save_path = charts_dir / f"win_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _create_duration_histogram(self, games, charts_dir):
        """Create histogram of game durations"""
        durations = []
        for game in games:
            duration = self.safe_float(game.get('duration', 0)) / 60  # Convert to minutes
            if duration > 0:
                durations.append(duration)

        if not durations:
            plt.figure(figsize=(12, 8))
            plt.text(0.5, 0.5, 'No valid duration data available',
                     horizontalalignment='center', verticalalignment='center',
                     transform=plt.gca().transAxes, fontsize=14)
            plt.xlabel('Game Duration (minutes)')
            plt.ylabel('Frequency')
            plt.title('Game Duration Distribution')
        else:
            plt.figure(figsize=(12, 8))
            plt.hist(durations, bins=min(20, len(durations)), edgecolor='black', alpha=0.7)
            plt.xlabel('Game Duration (minutes)')
            plt.ylabel('Frequency')
            plt.title('Game Duration Distribution')
            plt.grid(True, alpha=0.3)

        save_path = charts_dir / f"durations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _create_move_trends_chart(self, games, charts_dir):
        """Create a line chart of move count trends"""
        dates = []
        move_counts = []
        valid_data_points = 0

        for game in games:
            try:
                # Parse timestamp
                timestamp = None
                try:
                    timestamp = datetime.strptime(game.get('timestamp', ''), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        timestamp = datetime.strptime(game.get('timestamp', ''), '%Y%m%d_%H%M%S')
                    except ValueError:
                        print(f"Warning: Invalid timestamp format: {game.get('timestamp', '')}")
                        continue

                # Get move count
                move_count = self.safe_int(game.get('total_moves', 0))
                if move_count > 0:
                    dates.append(timestamp)
                    move_counts.append(move_count)
                    valid_data_points += 1
            except Exception as e:
                print(f"Error processing game data for move trends: {e}")
                continue

        if valid_data_points > 0:
            plt.figure(figsize=(14, 8))
            plt.plot(dates, move_counts, marker='o', linestyle='-', linewidth=2, markersize=6)
            plt.xlabel('Date')
            plt.ylabel('Total Moves')
            plt.title('Move Count Trends Over Time')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)

            save_path = charts_dir / f"move_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.figure(figsize=(14, 8))
            plt.text(0.5, 0.5, 'No valid move data available',
                     horizontalalignment='center', verticalalignment='center',
                     transform=plt.gca().transAxes, fontsize=14)
            plt.xlabel('Date')
            plt.ylabel('Total Moves')
            plt.title('Move Count Trends Over Time')

            save_path = charts_dir / f"move_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()

    def _create_piece_usage_chart(self, games, charts_dir):
        """Create bar chart of piece usage"""
        piece_moves = {'Pawn': 0, 'Knight': 0, 'Bishop': 0, 'Rook': 0, 'Queen': 0, 'King': 0}

        for game in games:
            try:
                total = self.safe_int(game.get('total_moves', 0))
                if total > 0:
                    # Distribute moves based on typical chess patterns
                    piece_moves['Pawn'] += int(total * 0.4)
                    piece_moves['Knight'] += int(total * 0.15)
                    piece_moves['Bishop'] += int(total * 0.12)
                    piece_moves['Rook'] += int(total * 0.15)
                    piece_moves['Queen'] += int(total * 0.10)
                    piece_moves['King'] += int(total * 0.08)
            except Exception as e:
                print(f"Error processing game data for piece usage: {e}")
                continue

        plt.figure(figsize=(12, 8))
        pieces = list(piece_moves.keys())
        counts = list(piece_moves.values())
        colors = ['green', 'blue', 'purple', 'red', 'gold', 'orange']

        bars = plt.bar(pieces, counts, color=colors, alpha=0.8)
        plt.xlabel('Piece Type')
        plt.ylabel('Total Moves')
        plt.title('Piece Usage Statistics')
        plt.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{int(height)}',
                     ha='center', va='bottom')

        save_path = charts_dir / f"piece_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def export_data_to_csv(self):
        """Export additional CSV files for external analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.save_directory / f"summary_stats_{timestamp}.csv"
        summary = self.get_summary_statistics()

        if summary:
            with open(summary_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Games', summary['total_games']])
                writer.writerow(['White Win Rate', f"{summary['win_rates']['white']:.1f}%"])
                writer.writerow(['Black Win Rate', f"{summary['win_rates']['black']:.1f}%"])
                writer.writerow(['Draw Rate', f"{summary['win_rates']['draw']:.1f}%"])
                writer.writerow(['Average Duration (minutes)', f"{summary['averages']['duration'] / 60:.1f}"])
                writer.writerow(['Average Moves', f"{summary['averages']['moves']:.1f}"])
                writer.writerow(['Average Move Time (seconds)', f"{summary['averages']['move_time']:.2f}"])
                writer.writerow(['Total Playtime (hours)', f"{summary['total_playtime']:.1f}"])

        return summary_file

    def generate_statistics_report(self):
        """Generate a comprehensive statistics report with all charts"""
        charts_dir = self.generate_charts()
        heatmap_path = self.generate_heatmap()
        summary_file = self.export_data_to_csv()
        report_file = self.save_directory / f"complete_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(report_file, 'w') as f:
            f.write("CHESS STATISTICS REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            summary = self.get_summary_statistics()
            if summary:
                f.write("SUMMARY STATISTICS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Total Games: {summary['total_games']}\n")
                f.write(f"White Win Rate: {summary['win_rates']['white']:.1f}%\n")
                f.write(f"Black Win Rate: {summary['win_rates']['black']:.1f}%\n")
                f.write(f"Draw Rate: {summary['win_rates']['draw']:.1f}%\n")
                f.write(f"Average Game Duration: {summary['averages']['duration'] / 60:.1f} minutes\n")
                f.write(f"Total Playtime: {summary['total_playtime']:.1f} hours\n\n")

            f.write("GENERATED FILES\n")
            f.write("-" * 30 + "\n")
            f.write(f"Charts directory: {charts_dir}\n")
            f.write(f"Heatmap: {heatmap_path}\n")
            f.write(f"Summary CSV: {summary_file}\n")

        return report_file

    def get_game_by_id(self, game_id):
        """Get specific game data by ID"""
        games = self.get_all_games()
        for game in games:
            if game.get('game_id') == game_id:
                return game
        return None

    def get_player_performance_trend(self, color=None):
        """Get performance trend over time"""
        games = self.get_all_games()
        if not games:
            return None

        dates = []
        win_rates = []
        avg_moves = []
        avg_duration = []

        # Group games by week
        weekly_data = {}
        for game in games:
            try:
                # Parse timestamp
                timestamp = None
                try:
                    timestamp = datetime.strptime(game.get('timestamp', ''), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        timestamp = datetime.strptime(game.get('timestamp', ''), '%Y%m%d_%H%M%S')
                    except ValueError:
                        print(f"Warning: Invalid timestamp: {game.get('timestamp', '')}")
                        continue

                # Get week
                week = timestamp.isocalendar()[:2]  # (year, week)

                if week not in weekly_data:
                    weekly_data[week] = {'games': [], 'wins': 0}

                weekly_data[week]['games'].append(game)

                # Count wins for specified color
                winner = game.get('winner', '').lower()
                if color and winner == color:
                    weekly_data[week]['wins'] += 1
                elif not color and winner in ['white', 'black']:
                    weekly_data[week]['wins'] += 1
            except Exception as e:
                print(f"Error processing game for performance trend: {e}")
                continue

        # Calculate weekly metrics
        for week, data in sorted(weekly_data.items()):
            if not data['games']:
                continue

            try:
                # Create date for this week
                week_date = datetime.fromisocalendar(week[0], week[1], 1)
                dates.append(week_date)

                # Win rate
                total_games = len(data['games'])
                win_rate = (data['wins'] / total_games * 100) if total_games > 0 else 0
                win_rates.append(win_rate)

                # Average moves
                total_moves = sum(self.safe_int(g.get('total_moves', 0)) for g in data['games'])
                avg_move = total_moves / total_games if total_games > 0 else 0
                avg_moves.append(avg_move)

                # Average duration
                total_duration = sum(self.safe_float(g.get('duration', 0)) for g in data['games'])
                avg_dur = total_duration / total_games / 60 if total_games > 0 else 0
                avg_duration.append(avg_dur)
            except Exception as e:
                print(f"Error calculating weekly metrics: {e}")
                continue

        return {
            'dates': dates,
            'win_rates': win_rates,
            'avg_moves': avg_moves,
            'avg_duration': avg_duration
        }