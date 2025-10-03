from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import csv
from game_predictorV1 import (
    get_team_id, 
    get_home_team_stats, 
    get_road_team_stats,
    get_league_avg_stats,
    get_win_probabilities
)
import time

def get_all_2024_25_games():
    """Fetch all games from 2024-25 season"""
    print("Fetching all 2024-25 games...")
    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_nullable='2024-25',
        league_id_nullable='00',
        season_type_nullable='Regular Season'
    )
    games = gamefinder.get_data_frames()[0]
    
    # Each game appears twice (once for each team), so we need to deduplicate
    games = games.sort_values('GAME_DATE')
    games['GAME_ID'] = games['GAME_ID'].astype(str)
    
    # Get unique games by taking the first occurrence of each GAME_ID
    unique_games = []
    seen_game_ids = set()
    
    for _, game in games.iterrows():
        game_id = game['GAME_ID']
        if game_id not in seen_game_ids:
            seen_game_ids.add(game_id)
            # Get both teams for this game
            game_data = games[games['GAME_ID'] == game_id]
            if len(game_data) == 2:
                team1 = game_data.iloc[0]
                team2 = game_data.iloc[1]
                
                # Determine home and away based on MATCHUP (contains vs or @)
                if ' vs. ' in team1['MATCHUP']:
                    home_team = team1
                    road_team = team2
                elif ' @ ' in team1['MATCHUP']:
                    home_team = team2
                    road_team = team1
                else:
                    continue
                
                unique_games.append({
                    'GAME_ID': game_id,
                    'GAME_DATE': home_team['GAME_DATE'],
                    'HOME_TEAM': home_team['TEAM_NAME'],
                    'HOME_TEAM_ID': home_team['TEAM_ID'],
                    'ROAD_TEAM': road_team['TEAM_NAME'],
                    'ROAD_TEAM_ID': road_team['TEAM_ID'],
                    'HOME_WL': home_team['WL'],
                    'ROAD_WL': road_team['WL']
                })
    
    return pd.DataFrame(unique_games)

def test_predictions(scale=28, output_file='prediction_results.csv'):
    """
    Test the prediction model on all 2024-25 games
    
    Args:
        scale: Scale parameter for get_win_probabilities (default 28)
        output_file: Name of CSV output file
    """
    # Get all games
    games_df = get_all_2024_25_games()
    print(f"Found {len(games_df)} games to analyze\n")
    
    # Get league averages once
    print("Fetching league average stats...")
    avg_stats = get_league_avg_stats()
    
    results = []
    correct_predictions = 0
    total_games = 0
    
    # Track team stats to avoid repeated API calls
    team_stats_cache = {}
    
    for idx, game in games_df.iterrows():
        try:
            print(f"Processing game {idx + 1}/{len(games_df)}: {game['HOME_TEAM']} vs {game['ROAD_TEAM']}")
            
            home_team_id = str(game['HOME_TEAM_ID'])
            road_team_id = str(game['ROAD_TEAM_ID'])
            
            # Get or cache home team stats
            if home_team_id not in team_stats_cache:
                print(f"  Fetching {game['HOME_TEAM']} home stats...")
                team_stats_cache[home_team_id] = get_home_team_stats(home_team_id)
                time.sleep(0.6)  # Rate limiting
            home_stats = team_stats_cache[home_team_id]
            
            # Get or cache road team stats
            if road_team_id not in team_stats_cache:
                print(f"  Fetching {game['ROAD_TEAM']} road stats...")
                team_stats_cache[road_team_id] = get_road_team_stats(road_team_id)
                time.sleep(0.6)  # Rate limiting
            road_stats = team_stats_cache[road_team_id]
            
            # Get win probabilities
            home_wpct = get_win_probabilities(home_stats, road_stats, avg_stats, scale=scale)
            road_wpct = 100 - home_wpct
            
            # Determine predicted and actual winners
            if home_wpct > road_wpct:
                predicted_winner = game['HOME_TEAM']
                predicted_winner_pct = home_wpct
                predicted_loser = game['ROAD_TEAM']
                predicted_loser_pct = road_wpct
            else:
                predicted_winner = game['ROAD_TEAM']
                predicted_winner_pct = road_wpct
                predicted_loser = game['HOME_TEAM']
                predicted_loser_pct = home_wpct
            
            # Determine actual winner
            if game['HOME_WL'] == 'W':
                actual_winner = game['HOME_TEAM']
                actual_loser = game['ROAD_TEAM']
            else:
                actual_winner = game['ROAD_TEAM']
                actual_loser = game['HOME_TEAM']
            
            # Check if prediction was correct
            is_correct = (predicted_winner == actual_winner)
            if is_correct:
                correct_predictions += 1
            total_games += 1
            
            results.append({
                'Winner': predicted_winner,
                'Winner Winning %': round(predicted_winner_pct, 2),
                'Loser': predicted_loser,
                'Loser Winning %': round(predicted_loser_pct, 2),
                'Actual Winner': actual_winner,
                'Actual Loser': actual_loser,
                'Scale': scale,
                'Correct': is_correct
            })
            
            print(f"  Prediction: {predicted_winner} ({predicted_winner_pct:.1f}%) | Actual: {actual_winner} | {'✓' if is_correct else '✗'}\n")
            
        except Exception as e:
            print(f"  Error processing game: {e}\n")
            continue
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    # Create summary statistics
    accuracy = (correct_predictions / total_games * 100) if total_games > 0 else 0
    
    summary_file = output_file.replace('.csv', '_summary.txt')
    with open(summary_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("NBA PREDICTION MODEL PERFORMANCE SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Season: 2024-25\n")
        f.write(f"Scale Parameter: {scale}\n")
        f.write(f"Total Games Analyzed: {total_games}\n")
        f.write(f"Correct Predictions: {correct_predictions}\n")
        f.write(f"Incorrect Predictions: {total_games - correct_predictions}\n")
        f.write(f"Accuracy: {accuracy:.2f}%\n\n")
        
        # Additional statistics
        if len(results_df) > 0:
            avg_winner_conf = results_df['Winner Winning %'].mean()
            f.write(f"Average Predicted Winner Confidence: {avg_winner_conf:.2f}%\n")
            
            # High confidence predictions (>70%)
            high_conf = results_df[results_df['Winner Winning %'] > 70]
            if len(high_conf) > 0:
                high_conf_accuracy = (high_conf['Correct'].sum() / len(high_conf) * 100)
                f.write(f"High Confidence (>70%) Predictions: {len(high_conf)}\n")
                f.write(f"High Confidence Accuracy: {high_conf_accuracy:.2f}%\n\n")
            
            # Close games (<55%)
            close_games = results_df[results_df['Winner Winning %'] < 55]
            if len(close_games) > 0:
                close_game_accuracy = (close_games['Correct'].sum() / len(close_games) * 100)
                f.write(f"Close Game (<55%) Predictions: {len(close_games)}\n")
                f.write(f"Close Game Accuracy: {close_game_accuracy:.2f}%\n")
    
    print(f"Summary saved to {summary_file}")
    print(f"\nOverall Accuracy: {accuracy:.2f}% ({correct_predictions}/{total_games})")
    
    return results_df

if __name__ == '__main__':
    # You can modify the scale parameter here to test different values
    scale_value = int(input("Enter scale value (25-30, default 28): ") or "28")
    
    print("\nStarting prediction analysis...\n")
    results = test_predictions(scale=scale_value)
    print("\nAnalysis complete!")