"""
Tournament Import Module

This module handles the parsing and importing of tournament data from Excel files.
Extracted from tournaments.py for better reusability with the chess-results crawler.
"""

import hashlib
import re
import os
import pandas as pd
from datetime import datetime
from datetime import datetime
from db.models import db, Player, Tournament, TournamentPlayer, Game


def detect_round_columns(header):
    """Detect which columns contain round results"""
    round_columns = []
    for col in header:
        col_str = str(col).strip()
        # Round columns patterns:
        # - Pure numbers: 1, 2, 3, etc.
        # - Rd/Round format: Rd 1, Round 1, etc.
        # - German format: 1.Rd, 2.Rd, etc.
        if (re.match(r'^\d+$', col_str) or 
            re.match(r'^(Rd|Round)\s*\d+$', col_str, re.IGNORECASE) or
            re.match(r'^\d+\.Rd$', col_str, re.IGNORECASE)):
            round_columns.append(col)
    return round_columns


def find_existing_player(name, shuffling=False):
    """Find an existing player in the database by name"""
    name = name.strip()
    if not name:
        return None
        
    if ',' in name:
        last, first = [n.strip() for n in name.split(',', 1)]
    else:
        parts = name.split()
        if len(parts) == 2:
            first, last = parts
        elif len(parts) > 2:
            first = parts[0]
            last = ' '.join(parts[1:])
        else:
            first = name
            last = ''
            
    # Lookup 1: Lastname Firstname
    player = Player.query.filter(
        db.func.lower(Player.first_name) == first.lower(),
        db.func.lower(Player.last_name) == last.lower()
    ).first()
    if player:
        return player
        
    # Lookup 2: Firstname Lastname
    player = Player.query.filter(
        db.func.lower(Player.first_name) == last.lower(),
        db.func.lower(Player.last_name) == first.lower()
    ).first()
    if player:
        return player

    # Replace common letter combinations with umlauts and try again
    name_with_umlauts = name.lower().replace('ae', 'ä').replace('oe', 'ö').replace('ue', 'ü').replace('sz', 'ß')
    if name_with_umlauts != name.lower():
        player = find_existing_player(name_with_umlauts)
        if player:
            return player
    
    if not shuffling:
        # shuffle name parts: move the first part to the last
        name_parts = name.split()
        for i in range(len(name_parts)):
            shuffled_name = ' '.join(name_parts[i:] + name_parts[:i])
            player = find_existing_player(shuffled_name, shuffling=True)
            if player:
                return player

    return None

def find_header_row(df):
    """Find the row containing column headers"""
    for idx, row in df.iterrows():
        values = [str(v).strip() for v in row]
        if 'Name' in values:
            return idx
    raise ValueError("Header row not found")


def detect_result_format(df, header, header_row_idx):
    """Detect the format used for storing game results"""
    # Check for team tournament indicators
    for i in range(min(20, len(df))):  # Check first 20 rows
        row = [str(v).strip() for v in df.iloc[i]]
        for cell in row:
            # Look for Captain/Kapitän indicators
            if ('Captain:' in cell or 'Kapitän:' in cell or 
                'Team-Composition' in cell or 
                'with round-results' in cell):
                return 'team'
    
    # Check if we have team names with ratings in parentheses like "Hörbranz 1 (RtgAvg:2062, TB1: 18 / TB2: 49,5)"
    for i in range(header_row_idx):
        row = [str(v).strip() for v in df.iloc[i]]
        for cell in row:
            if re.match(r'.*\(RtgAvg:\d+.*TB1:.*TB2:.*\)', cell):
                return 'team'

    round_columns = detect_round_columns(header)
    for i in range(header_row_idx + 1, len(df)):
        row = [str(v).strip() for v in df.iloc[i]]
        if not row:
            break
        data = dict(zip(header, [str(v).strip() for v in row]))
        if not data.get('Name', '') or data.get('Name', '') == "nan":
            break

        for r in round_columns:
            round_result = data.get(r)
            if round_result in ['*', '***']:
                continue
            if re.match(r'^\d+ \d+$', round_result):
                return 'pair'
            if re.match(r'^\d+[wsb][10½+]$', round_result):
                return 'complex'

    return 'simple'


def set_player_active_if_youth(player):
    """Set player to active only if their category starts with 'U' (youth categories), excluding U20"""
    if player and player.kat and player.kat.startswith('U') and player.kat.upper() != 'U20':
        player.is_active = True
        db.session.add(player)


def parse_team_players(df, tournament):
    """Parse player data from team tournament Excel file"""
    ranked_players = []
    games_to_create = []  # Store game data to create after players are committed
    player_count = 0  # Track number of players processed
    
    # Find all team sections by looking for team headers and player data
    i = 0
    while i < len(df):
        row_data = [str(v).strip() if v is not None else '' for v in df.iloc[i]]
        row_text = ' '.join(row_data).strip()
        
        # Look for team header (e.g., "1. Rankweil 1 (RtgAvg:2125, TB1: 18 / TB2: 48)")
        if any(pattern in row_text for pattern in ['RtgAvg:', 'TB1:', 'TB2:']):
            print(f"Found team header at row {i}: {row_text}")
            i += 1
            continue
            
        # Look for captain line
        if row_text.startswith('Captain:'):
            print(f"Found captain at row {i}: {row_text}")
            i += 1
            continue
            
        # Look for player data header (Bo., Name, Rtg, FED, etc.)
        if 'Bo.' in row_text and 'Name' in row_text:
            print(f"Found player header at row {i}: {row_text}")
            # Parse the header
            header = [str(v).strip() if v is not None else '' for v in df.iloc[i]]
            header = [h for h in header if h]  # Remove empty columns
            
            # Find relevant columns
            name_col = None
            points_col = None
            round_columns = []
            
            for idx, col in enumerate(header):
                col_lower = col.lower()
                if 'name' in col_lower:
                    name_col = idx
                elif any(p in col_lower for p in ['pts', 'punkte', 'points']):
                    points_col = idx
                elif col.isdigit() or any(r in col_lower for r in ['rd.', 'runde', 'round']):
                    round_columns.append((idx, col))
            
            if name_col is None:
                print(f"Warning: No name column found in header: {header}")
                i += 1
                continue
                
            print(f"Found round columns: {round_columns}")
                
            # Parse players in this team
            i += 1
            while i < len(df):
                player_row = [str(v).strip() if v is not None else '' for v in df.iloc[i]]
                
                # Check if this is still player data
                if not player_row or len(player_row) <= name_col or not player_row[name_col] or player_row[name_col] == 'nan':
                    break
                    
                # Check if we hit the next team header
                player_row_text = ' '.join(player_row).strip()
                if any(pattern in player_row_text for pattern in ['RtgAvg:', 'TB1:', 'TB2:', 'Captain:']):
                    break
                
                name = player_row[name_col].strip()
                if not name or name == 'nan':
                    break
                    
                # Parse points
                try:
                    points = float(player_row[points_col]) if points_col is not None and points_col < len(player_row) else 0
                except (ValueError, TypeError, IndexError):
                    points = 0
                
                # Find or note player
                player = find_existing_player(name)
                if player:
                    set_player_active_if_youth(player)
                else:
                    print(f'Player not found: {name}')

                tp = TournamentPlayer(
                    tournament_id=tournament.id,
                    player_id=player.id if player else None,
                    name=name,
                    ranking=None,  # No individual rankings in team tournaments
                    points=points,
                    tiebreak1=0,  # Not used for team tournaments
                    tiebreak2=0   # Not used for team tournaments
                )
                ranked_players.append(tp)
                db.session.add(tp)
                
                # Parse individual round results and store for later game creation
                games_count = 0
                for round_idx, round_col in round_columns:
                    if round_idx < len(player_row):
                        round_result = player_row[round_idx].strip()
                        if round_result and round_result != 'nan' and round_result not in ['*', '***', '+', '-']:
                            games_count += 1
                            # Store game data to create after tp is committed
                            games_to_create.append({
                                'tournament_player': tp,
                                'round_number': int(round_col) if round_col.isdigit() else games_count,
                                'result': round_result
                            })
                
                player_count += 1
                print(f"Added player {player_count}: {name}, points: {points}, games: {games_count}")
                
                i += 1
            continue
        
        i += 1
    
    if not ranked_players:
        raise ValueError('No valid player data found in team tournament')

    # Commit tournament players first so they get IDs
    db.session.flush()
    
    # Now create games with proper tournament player IDs
    from db.models import Game
    for game_data in games_to_create:
        tp = game_data['tournament_player']
        game = Game(
            tournament_id=tournament.id,
            player_id=tp.id,
            round_number=game_data['round_number'],
            player_color=None,  # No color info available in team tournaments  
            opponent_id=None,  # No opponent info in team tournaments
            result=game_data['result']
        )
        db.session.add(game)

    print(f"Total players imported: {len(ranked_players)}")
    print(f"Total games created: {len(games_to_create)}")
    return ranked_players, [], {}, len(games_to_create)  # Return games count for team tournaments


def parse_players(df, header, header_row_idx, tournament, result_format):
    """Parse player data from the Excel file"""
    # Handle team tournaments differently
    if result_format == 'team':
        return parse_team_players(df, tournament)
        
    round_columns = detect_round_columns(header)
    
    # Find scoring columns (usually after round columns)
    # Look for various patterns for scoring columns
    wtg1_column = None
    wtg2_column = None
    wtg3_column = None
    
    # Common patterns for scoring columns
    score_patterns = [
        'wtg', 'pts', 'punkte', 'points', 'pkte', 'total', 'sum', 'erg', 'tb1'
    ]
    tiebreak_patterns = [
        'buchh', 'buchhol', 'bh', 'sb', 'sonn', 'sonneborn', 'prog', 'progress', 'tb2', 'tb3'
    ]
    
    # Special handling for TB1, TB2, TB3 pattern (common in chess-results.com)
    tb1_col = None
    tb2_col = None
    tb3_col = None
    pts_col = None
    
    for col in header:
        col_str = str(col).upper().strip()
        if col_str == 'TB1':
            tb1_col = col
        elif col_str == 'TB2':
            tb2_col = col
        elif col_str == 'TB3':
            tb3_col = col
        elif col_str in ['PTS', 'PKT', 'PTS.', 'PKT.', 'POINTS', 'POINTS.', 'PUNKTE', 'PUNKTE.']:
            pts_col = col
    
    # If we found TB columns, check if there's also an explicit points column
    if tb1_col:
        if pts_col:
            # If both TB1 and explicit points column exist, use points column for main score
            wtg1_column = pts_col
            wtg2_column = tb1_col  # TB1 becomes first tiebreak
            wtg3_column = tb2_col  # TB2 becomes second tiebreak
            print(f"Detected mixed pattern: Pts='{pts_col}', TB1='{tb1_col}', TB2='{tb2_col}', TB3='{tb3_col}'")
        else:
            # Only TB columns, assume TB1 contains main points (old behavior)
            wtg1_column = tb1_col
            wtg2_column = tb2_col
            wtg3_column = tb3_col
            print(f"Detected TB pattern: TB1='{tb1_col}', TB2='{tb2_col}', TB3='{tb3_col}'")
    elif pts_col:
        # No TB columns but we found an explicit points column
        # Look for Wtg1/Wtg2/Wtg3 or other tiebreak columns
        wtg1_column = pts_col
        
        # Find tiebreak columns after the points column
        pts_idx = header.index(pts_col)
        for i in range(pts_idx + 1, len(header)):
            col_name = str(header[i]).strip()
            if col_name and col_name != 'nan':
                if not wtg2_column:
                    wtg2_column = header[i]
                elif not wtg3_column:
                    wtg3_column = header[i]
                    break
        
        print(f"Detected points pattern: Pts='{pts_col}', Wtg1='{wtg2_column}', Wtg2='{wtg3_column}'")
    else:
        # Find scoring columns with original logic
        for i, col in enumerate(header):
            col_lower = str(col).lower().strip()
            
            # First scoring column (main points)
            if not wtg1_column:
                for pattern in score_patterns:
                    if pattern in col_lower:
                        wtg1_column = col
                        break
            
            # Second scoring column (first tiebreak)
            elif not wtg2_column:
                for pattern in tiebreak_patterns:
                    if pattern in col_lower:
                        wtg2_column = col
                        break
                # If no tiebreak pattern found, try next column after main score
                if not wtg2_column and i > 0:
                    prev_col = str(header[i-1]).lower().strip()
                    for pattern in score_patterns:
                        if pattern in prev_col:
                            wtg2_column = col
                            break
            
            # Third scoring column (second tiebreak)
            elif not wtg3_column:
                for pattern in tiebreak_patterns:
                    if pattern in col_lower:
                        wtg3_column = col
                        break
    
    # If we still haven't found scoring columns, use positional logic
    if not wtg1_column and round_columns:
        last_round_idx = header.index(round_columns[-1])
        # Look for numeric columns after the last round column
        for i in range(last_round_idx + 1, len(header)):
            col_name = str(header[i]).strip()
            if col_name and col_name != 'nan':
                if not wtg1_column:
                    wtg1_column = header[i]
                elif not wtg2_column:
                    wtg2_column = header[i]
                elif not wtg3_column:
                    wtg3_column = header[i]
                    break

    print(f"Detected scoring columns: Wtg1='{wtg1_column}', Wtg2='{wtg2_column}', Wtg3='{wtg3_column}'")
    
    if not wtg1_column:
        # Last resort: look for any numeric column that might contain scores
        for col in header:
            col_str = str(col).strip()
            if col_str and col_str != 'nan' and col_str.lower() != 'name':
                # Check if this column contains numeric data
                try:
                    test_data = []
                    for i in range(header_row_idx + 1, min(header_row_idx + 6, len(df))):
                        row = [str(v).strip() for v in df.iloc[i]]
                        if len(row) > header.index(col):
                            data = dict(zip(header, row))
                            val = data.get(col, '')
                            if val and val != 'nan':
                                test_data.append(float(val))
                    
                    if len(test_data) > 0:  # Found numeric data
                        wtg1_column = col
                        print(f"Found numeric column for main score: '{wtg1_column}'")
                        break
                except (ValueError, IndexError):
                    continue
    
    if not wtg1_column:
        raise ValueError("No scoring column found. Available columns: " + ", ".join([str(c) for c in header]))

    ranked_players = []
    rank = 1

    for i in range(header_row_idx + 1, len(df)):
        row = [str(v).strip() for v in df.iloc[i]]
        if not row:
            break
        data = dict(zip(header, [str(v).strip() for v in row]))
        if not data.get('Name', '') or data.get('Name', '') == "nan":
            break

        name = data.get('Name', '').strip()
        player = find_existing_player(name)
        if player:
            set_player_active_if_youth(player)
        else:
            print(f'Player not found: {name}')

        # Parse rank from first column if available
        if data.get(header[0]) != "nan":
            try:
                rank = int(data.get(header[0], 0))
            except ValueError:
                pass

        # Parse scoring data
        try:
            points = float(data.get(wtg1_column, 0)) if wtg1_column else 0
        except (ValueError, TypeError):
            points = 0
            
        try:
            tiebreak1 = float(data.get(wtg2_column, 0)) if wtg2_column else 0
        except (ValueError, TypeError):
            tiebreak1 = 0
            
        try:
            tiebreak2 = float(data.get(wtg3_column, 0)) if wtg3_column else 0
        except (ValueError, TypeError):
            tiebreak2 = 0

        tp = TournamentPlayer(
            tournament_id=tournament.id,
            player_id=player.id if player else None,
            name=name,
            ranking=rank,
            points=points,
            tiebreak1=tiebreak1,
            tiebreak2=tiebreak2
        )
        ranked_players.append(tp)
        db.session.add(tp)

    if not ranked_players:
        raise ValueError('No valid player data found')

    rank_dict = {tp.ranking: tp for tp in ranked_players}
    return ranked_players, round_columns, rank_dict, 0  # 0 games for non-team tournaments (parsed separately)


def parse_games(df, header, header_row_idx, round_columns, ranked_players, tournament, result_format, rank_dict):
    """Parse game results from the Excel file"""
    imported_games = 0
    rank = 0
    
    for i in range(header_row_idx + 1, len(df)):
        row = [str(v).strip() for v in df.iloc[i]]
        if not row:
            break
        data = dict(zip(header, [str(v).strip() for v in row]))
        if not data.get('Name', '') or data.get('Name', '') == "nan":
            break

        rank += 1
        if rank > len(ranked_players):
            break
            
        player = ranked_players[rank - 1]
        if not player:
            continue  # Skip if no player at this rank

        for r in range(len(round_columns)):
            round_result = data.get(round_columns[r])
            if round_result in ['*', '***', '+'] or not round_result:
                continue

            player_color = None
            opponent = None
            result = None

            if result_format == 'simple':
                if round_result in ['*', '***', '+']:
                    continue
                round_num = r + 1
                opponent_rank = round_num
                if opponent_rank not in rank_dict or opponent_rank == player.ranking:
                    continue
                opponent = rank_dict[opponent_rank]
                result = round_result
                
            elif result_format == 'team':
                if round_result not in ['1', '0', '½']:
                    continue
                # For team tournaments, no opponent, just record result but don't create Game
                continue
                
            elif result_format == 'pair':
                if round_result == '+':
                    continue
                parts = round_result.split()
                if len(parts) != 2:
                    print(f"DEBUG: Invalid pair format {round_result} for {player.name}")
                    continue
                try:
                    opponent_nr = int(parts[0])
                    result = parts[1]
                except ValueError:
                    print(f"DEBUG: Invalid numbers in {round_result} for {player.name}")
                    continue
                if opponent_nr < 1 or opponent_nr > len(ranked_players):
                    print(f"DEBUG: Opponent number {opponent_nr} out of range for {player.name}")
                    continue
                opponent = ranked_players[opponent_nr - 1]
                if opponent == player:
                    print(f"DEBUG: Self opponent for {player.name}")
                    continue
                    
            else:  # complex format
                if round_result == '+':
                    continue
                
                # Handle various result formats
                opponent = None
                result = None
                player_color = None
                
                # Handle bye rounds and forfeit losses
                if round_result in ['-1', '-½', '-0.5']:
                    # Bye rounds: -1 (full point bye), -½ (half point bye)
                    continue  # Skip creating game record for byes
                elif round_result == '0':
                    # Forfeit loss with no opponent specified
                    continue  # Skip if no opponent info
                
                # Try standard complex format: "123w1" or "45b½"
                m = re.match(r'^(\d+)([wsb])([10½+])$', round_result)
                if m:
                    opponent_nr = int(m.group(1))
                    if opponent_nr < 1 or opponent_nr > len(ranked_players):
                        continue
                    opponent = ranked_players[opponent_nr - 1]
                    result = m.group(3)
                    color = m.group(2)
                    if color == 'w':
                        player_color = 'white'
                    elif color in ['s', 'b']:
                        player_color = 'black'
                else:
                    # Try withdrawal/forfeit formats: "123w-" or "45b-"
                    m = re.match(r'^(\d+)([wsb])-$', round_result)
                    if m:
                        opponent_nr = int(m.group(1))
                        if opponent_nr < 1 or opponent_nr > len(ranked_players):
                            continue
                        opponent = ranked_players[opponent_nr - 1]
                        result = '1'  # Win by forfeit/withdrawal
                        color = m.group(2)
                        if color == 'w':
                            player_color = 'white'
                        elif color in ['s', 'b']:
                            player_color = 'black'
                    else:
                        # Try half-point bye with opponent: "-½" alone already handled above
                        print(f'Invalid round result, assuming skip: {round_result} for {player.name}')
                        continue

            # Create game record for non-team tournaments
            if result_format != 'team' and opponent and result:
                if player.id == opponent.id:
                    print(f'Player cannot play against themselves: {player.name}')
                    continue
                    
                game = Game(
                    tournament_id=tournament.id,
                    player_id=player.id,  # This is the TournamentPlayer.id
                    player_color=player_color,
                    opponent_id=opponent.id,  # This is the TournamentPlayer.id
                    round_number=r + 1,
                    result=result
                )
                db.session.add(game)
                imported_games += 1

    return imported_games


def create_best_of_3_games(ranked_players, tournament, df):
    """
    Create game records for Best of 3 matches based on final scores.
    
    Args:
        ranked_players: List of TournamentPlayer objects (should be 2 players)
        tournament: Tournament object
        df: DataFrame containing the tournament data
        
    Returns:
        int: Number of games created
    """
    if len(ranked_players) != 2:
        return 0
        
    player1, player2 = ranked_players[0], ranked_players[1]
    
    # Get scores from TB1 column (points/game-points in Best of 3)
    # TB1 maps to the points field in the tournament player
    player1_score = int(player1.points) if player1.points else 0
    player2_score = int(player2.points) if player2.points else 0
    
    print(f"Creating Best of 3 games: {player1.name} {player1_score}-{player2_score} {player2.name}")
    
    imported_games = 0
    
    # Create individual game records based on the final score
    total_games = player1_score + player2_score
    
    for round_num in range(1, total_games + 1):
        # Determine result for this game
        # For a 2-0 result: rounds 1 and 2 go to winner
        # For a 2-1 result: rounds 1,2 to winner, round 3 to loser
        if round_num <= player1_score:
            # Player1 wins this game
            player1_result = "1"
            player2_result = "0"
        else:
            # Player2 wins this game  
            player1_result = "0"
            player2_result = "1"
        
        # Create game from player1's perspective
        game1 = Game(
            tournament_id=tournament.id,
            round_number=round_num,
            player_id=player1.id,
            opponent_id=player2.id,
            result=player1_result,
            player_color="white" if round_num % 2 == 1 else "black"
        )
        
        # Create game from player2's perspective
        game2 = Game(
            tournament_id=tournament.id,
            round_number=round_num,
            player_id=player2.id,
            opponent_id=player1.id,
            result=player2_result,
            player_color="black" if round_num % 2 == 1 else "white"
        )
        
        db.session.add(game1)
        db.session.add(game2)
        imported_games += 2
        
        print(f"   Round {round_num}: {player1.name} ({player1_result}) vs {player2.name} ({player2_result})")
    
    print(f"Created {imported_games} game records for Best of 3 match")
    return imported_games


def parse_cross_table_games(cross_table_file, ranked_players, tournament):
    """
    Parse cross table Excel file to extract round-by-round game results.
    
    Args:
        cross_table_file: Path to cross table Excel file
        ranked_players: List of TournamentPlayer objects
        tournament: Tournament object
        
    Returns:
        int: Number of games created
    """
    if not cross_table_file or not os.path.exists(cross_table_file):
        return 0
        
    try:
        import pandas as pd
        df = pd.read_excel(cross_table_file)
        
        # Create a mapping from player names to TournamentPlayer objects
        player_map = {}
        for tp in ranked_players:
            # Handle both "Last, First" and "First Last" formats
            name_variants = [tp.name]
            if ',' in tp.name:
                last, first = [n.strip() for n in tp.name.split(',', 1)]
                name_variants.append(f"{first} {last}")
                name_variants.append(f"{last}, {first}")
            player_map[tp.name] = tp
            for variant in name_variants:
                player_map[variant] = tp
        
        imported_games = 0
        current_round = 0
        
        print(f"Parsing cross table from {cross_table_file}")
        
        # Look for round headers and game results
        for i, row in df.iterrows():
            row_data = [str(v).strip() if pd.notna(v) else '' for v in row]
            
            # Check if this is a round header
            for cell in row_data:
                if 'round' in cell.lower() and ('on' in cell.lower() or any(char.isdigit() for char in cell)):
                    # Extract round number
                    import re
                    round_match = re.search(r'round\s+(\d+)', cell.lower())
                    if round_match:
                        current_round = int(round_match.group(1))
                        print(f"Found Round {current_round}")
                        break
            
            # Check if this is a game result row
            if current_round > 0 and len(row_data) >= 8:
                # Check if this row has the game structure: Bo., No., Rtg, '', White, Result, '', Black, Rtg, No.
                if (row_data[0] and row_data[0].isdigit() and  # Bo. number
                    row_data[4] and  # White player name
                    row_data[5] and '-' in row_data[5] and  # Result
                    row_data[7]):  # Black player name
                    
                    white_name = row_data[4].strip()
                    result_cell = row_data[5].strip()
                    black_name = row_data[7].strip()
                    
                    # Find players in our mapping
                    white_player = player_map.get(white_name)
                    black_player = player_map.get(black_name)
                    
                    if white_player and black_player:
                        # Parse result
                        result_parts = result_cell.split('-')
                        if len(result_parts) == 2:
                            white_result = result_parts[0].strip()
                            black_result = result_parts[1].strip()
                            
                            # Convert to standard format
                            if white_result == '½':
                                white_result = '0.5'
                            if black_result == '½':
                                black_result = '0.5'
                            
                            # Create game records
                            game1 = Game(
                                tournament_id=tournament.id,
                                round_number=current_round,
                                player_id=white_player.id,
                                opponent_id=black_player.id,
                                result=white_result,
                                player_color="white"
                            )
                            
                            game2 = Game(
                                tournament_id=tournament.id,
                                round_number=current_round,
                                player_id=black_player.id,
                                opponent_id=white_player.id,
                                result=black_result,
                                player_color="black"
                            )
                            
                            db.session.add(game1)
                            db.session.add(game2)
                            imported_games += 2
                            
                            print(f"   Round {current_round}: {white_name} ({white_result}) vs {black_name} ({black_result})")
                    else:
                        if not white_player:
                            print(f"   Warning: White player '{white_name}' not found in database")
                        if not black_player:
                            print(f"   Warning: Black player '{black_name}' not found in database")
        
        print(f"Imported {imported_games} games from cross table")
        return imported_games
        
    except Exception as e:
        print(f"Error parsing cross table: {e}")
        return 0


def import_tournament_from_excel(file_path, tournament_details):
    try:
        # Load Excel file
        df = pd.read_excel(file_path, header=None)
        
        # Generate checksum if not provided
        if not tournament_details.get('checksum'):
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            tournament_details['checksum'] = sha256.hexdigest()

        # Check if tournament already imported
        if Tournament.query.filter_by(checksum=tournament_details['checksum']).first():
            raise ValueError('Tournament already imported')
        
        # Find header row and parse structure
        header_row_idx = find_header_row(df)
        header = [str(v).strip() for v in df.iloc[header_row_idx]]
        if not header:
            raise ValueError("No valid header found")

        # Detect result format
        result_format = detect_result_format(df, header, header_row_idx)
        print(f"Detected result format: {result_format}")

        # Check if any players can be mapped before creating tournament
        mapped_players_count = 0
        for i in range(header_row_idx + 1, len(df)):
            row = [str(v).strip() for v in df.iloc[i]]
            if not row:
                break
            data = dict(zip(header, [str(v).strip() for v in row]))
            if not data.get('Name', '') or data.get('Name', '') == "nan":
                break
            name = data.get('Name', '').strip()
            player = find_existing_player(name)
            if player:
                mapped_players_count += 1
                break  # We only need to find one mapped player

        if mapped_players_count == 0:
            print(f"Warning: No players from this tournament could be mapped to existing players. Importing tournament anyway.")

        # Convert date string to Python date object if needed
        if 'date' in tournament_details and isinstance(tournament_details['date'], str):
            try:
                from datetime import datetime
                tournament_details['date'] = datetime.strptime(tournament_details['date'], '%Y-%m-%d').date()
            except ValueError as e:
                tournament_details['date'] = None
        

        # Create tournament
        print(f"Creating tournament: {tournament_details.get('name')}")
        tournament = Tournament(
            name=tournament_details.get('name'), 
            checksum=tournament_details.get('checksum'), 
            date=tournament_details.get('date'), 
            location=tournament_details.get('location'),
            is_team=(result_format == 'team'),
            chess_results_id=tournament_details.get('id'),
            chess_results_url=tournament_details.get('tournament_url'),
            elo_rating=tournament_details.get('elo_calculation'),
            time_control=tournament_details.get('time_control'),
            rounds=tournament_details.get('number_of_rounds'),
            imported_at=datetime.now()
        )
        db.session.add(tournament)
        db.session.flush()

        # Parse players and games
        ranked_players, round_columns, rank_dict, team_games_count = parse_players(df, header, header_row_idx, tournament, result_format)
        db.session.flush()
        
        for i, p in enumerate(ranked_players):
            if result_format == 'team':
                print(f"Team Player {i+1}: {p.name} (ID: {p.player_id}) - {p.points} pts")
            else:
                print(f"Ranked Player: {p.ranking} - {p.name} (ID: {p.player_id})")

        # For team tournaments, games are already created in parse_team_players
        if result_format == 'team':
            imported_games = team_games_count
        else:
            imported_games = parse_games(df, header, header_row_idx, round_columns, ranked_players, tournament, result_format, rank_dict)

        # Special handling for Best of 3 matches (2 players, 0 games from normal parsing)
        if len(ranked_players) == 2 and imported_games == 0:
            imported_games = create_best_of_3_games(ranked_players, tournament, df)
        
        # Special handling for results-only tournaments (multiple players, final standings but no games)
        elif len(ranked_players) > 2 and imported_games == 0:
            print(f"Results-only tournament detected: {len(ranked_players)} players with final standings but no individual games")
            print("This is typical for tournaments where only final results are published")
            # No need to create artificial games - we have the final standings which is sufficient

        db.session.commit()
        
        return {
            'success': True,
            'tournament_id': tournament.id,
            'tournament_name': tournament_details.get('name'),
            'location': tournament_details.get('location'),
            'date': tournament_details.get('date').isoformat() if tournament_details.get('date') else None,
            'imported_games': imported_games,
            'imported_players': len(ranked_players),
            'mapped_players': mapped_players_count
        }

    except Exception as e:
        db.session.rollback()
        raise e
