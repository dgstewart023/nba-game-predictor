from nba_api.stats.endpoints import leaguedashteamstats
import pandas as pd
import csv

def get_team_id(identifier):
    """
    Get team ID by team name or abbreviation.
    
    Args:
        identifier: Team name (e.g., "Los Angeles Lakers") or 
                   abbreviation (e.g., "LAL")
    
    Returns:
        Team ID as string, or None if not found
    """
    with open('nba_teams.csv', 'r') as file:
        csv_reader = csv.reader(file)

        identifier = identifier.lower().strip()

        next(csv_reader)
        for row in csv_reader:
            team_name = row[0].lower()
            team_abb = row[1].lower()
            team_id = row[2]
            if (identifier == team_abb or
                identifier == team_name or
                identifier in team_name):
                return team_id
            
        return None

def get_league_avg_stats():
    """
    Returns a DataFrame with league averages
    """
    stats = leaguedashteamstats.LeagueDashTeamStats(
        season='2024-25',
        measure_type_detailed_defense='Four Factors',
        per_mode_detailed='PerGame'
    )
    df = stats.get_data_frames()[0]
    
    league_avg = pd.DataFrame({
        'TEAM_NAME': ['LEAGUE AVERAGE'],
        'EFG_PCT': [df['EFG_PCT'].mean()],
        'TM_TOV_PCT': [df['TM_TOV_PCT'].mean()],
        'OREB_PCT': [df['OREB_PCT'].mean()],
        'FTA_RATE': [df['FTA_RATE'].mean()]
    })
    
    return league_avg

def get_single_team_stats(team_id):
    """Get efficiency stats for one team"""
    stats = leaguedashteamstats.LeagueDashTeamStats(
        season='2024-25',
        measure_type_detailed_defense='Four Factors',
        per_mode_detailed='PerGame'
    )
    df = stats.get_data_frames()[0]
    
    team_data = df[df['TEAM_ID'] == int(team_id)]

    four_factors_data = team_data[['TEAM_NAME',
                            'EFG_PCT',
                            'TM_TOV_PCT',
                            'OREB_PCT',
                            'FTA_RATE',
                            'OPP_EFG_PCT',
                            'OPP_TOV_PCT',
                            'OPP_OREB_PCT',
                            'OPP_FTA_RATE']]
    return four_factors_data

def get_win_probabilities(teamA, teamB, avg):
    teamA_EFG = ((teamA['EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]) - 
                (teamB['OPP_EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]))
    teamB_EFG = ((teamB['EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]) - 
                (teamA['OPP_EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]))
    teamA_TOV = ((teamB['OPP_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]) - 
                (teamA['TM_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]))
    teamB_TOV = ((teamA['OPP_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]) - 
                (teamB['TM_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]))
    teamA_OREB = ((teamA['OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]) - 
                (teamB['OPP_OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]))
    teamB_OREB = ((teamB['OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]) - 
                (teamA['OPP_OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]))
    teamA_FT = ((teamA['FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]) - 
                (teamB['OPP_FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]))
    teamB_FT = ((teamB['FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]) - 
                (teamA['OPP_FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]))
    teamA_weighted = ((teamA_EFG * 0.4) + (teamA_TOV * 0.25) + 
                      (teamA_OREB * 0.20) + (teamA_FT * 0.15))
    teamB_weighted = ((teamB_EFG * 0.4) + (teamB_TOV * 0.25) + 
                      (teamB_OREB * 0.20) + (teamB_FT * 0.15))
    raw_diff = (teamA_weighted - teamB_weighted) * 28
    teamA_WPCT = 1 / (1 + 10**(-raw_diff / 15)) 

    return teamA_WPCT * 100


if __name__ == '__main__':
    home = input("Enter Home Team: ")
    away = input("Enter Away Team: ")

    home_id = get_team_id(home)
    away_id = get_team_id(away)

    home_stats = get_single_team_stats(home_id)
    away_stats = get_single_team_stats(away_id)
    avg_stats = get_league_avg_stats()

    home_WPCT = get_win_probabilities(home_stats, away_stats, avg_stats)
    away_WPCT = 100 - home_WPCT

    print(f'{home_stats['TEAM_NAME'].iloc[0]} has a {home_WPCT}% chance of winning')
    print(f'{away_stats['TEAM_NAME'].iloc[0]} has a {away_WPCT}% chance of winning')