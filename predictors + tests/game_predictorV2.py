from nba_api.stats.endpoints import (leaguedashteamstats,
                                     teamdashboardbygeneralsplits)
import pandas as pd
import csv

"""
Game Predictor V1 uses the Dean Oliver's Four Factors, while using a simple
point spread method of differentiating the teams skill.
"""


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
                return team_id, team_abb.upper()

        return None


def get_league_avg_stats():
    """
    Returns a DataFrame with league averages
    """
    stats = leaguedashteamstats.LeagueDashTeamStats(
        season='2024-25',
        measure_type_detailed_defense='Four Factors'
    )
    df = stats.get_data_frames()[0]

    nba_df = df[(df['TEAM_ID'] >= 1610612737) & (df['TEAM_ID'] <= 1610612766)]
    
    basic_stats = leaguedashteamstats.LeagueDashTeamStats(
        season='2024-25',
        per_mode_detailed='PerGame'
    )
    basic_df = basic_stats.get_data_frames()[0]

    nba_basic_df = basic_df[(basic_df['TEAM_ID'] >= 1610612737) & (basic_df['TEAM_ID'] <= 1610612766)]

    league_avg = pd.DataFrame({
        'TEAM_NAME': ['LEAGUE AVERAGE'],
        'EFG_PCT': [nba_df['EFG_PCT'].mean()],
        'TM_TOV_PCT': [nba_df['TM_TOV_PCT'].mean()],
        'OREB_PCT': [nba_df['OREB_PCT'].mean()],
        'FTA_RATE': [nba_df['FTA_RATE'].mean()],
        'PTS': [nba_basic_df['PTS'].mean()]
    })

    return league_avg


def get_team_stats(team_id, location):
    """
    Get Four Factors stats for a team at a specific location
    
    Args:
        team_id: NBA team ID
        location: 'Home' or 'Road'
    
    Returns:
        DataFrame with Four Factors data
    """
    stats = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
        team_id=team_id,
        season='2024-25',
        measure_type_detailed_defense='Four Factors'
    )
    df = stats.get_data_frames()[1]

    location_data = df[df['TEAM_GAME_LOCATION'] == location]

    four_factors_data = location_data[['EFG_PCT',
                                        'TM_TOV_PCT',
                                        'OREB_PCT',
                                        'FTA_RATE',
                                        'OPP_EFG_PCT',
                                        'OPP_TOV_PCT',
                                        'OPP_OREB_PCT',
                                        'OPP_FTA_RATE']]
    return four_factors_data


def get_win_probabilities(home, road, avg):
    home_EFG = ((home['EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]) -
                 (road['OPP_EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]))
    road_EFG = ((road['EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]) -
                 (home['OPP_EFG_PCT'].iloc[0] - avg['EFG_PCT'].iloc[0]))
    home_TOV = ((road['OPP_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]) -
                 (home['TM_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]))
    road_TOV = ((home['OPP_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]) -
                 (road['TM_TOV_PCT'].iloc[0] - avg['TM_TOV_PCT'].iloc[0]))
    home_OREB = ((home['OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]) -
                  (road['OPP_OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]))
    road_OREB = ((road['OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]) -
                  (home['OPP_OREB_PCT'].iloc[0] - avg['OREB_PCT'].iloc[0]))
    home_FT = ((home['FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]) -
                (road['OPP_FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]))
    road_FT = ((road['FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]) -
                (home['OPP_FTA_RATE'].iloc[0] - avg['FTA_RATE'].iloc[0]))
    home_weighted = ((home_EFG * 0.4) + (home_TOV * 0.25) +
                      (home_OREB * 0.20) + (home_FT * 0.15))
    road_weighted = ((road_EFG * 0.4) + (road_TOV * 0.25) +
                      (road_OREB * 0.20) + (road_FT * 0.15))
    net_diff = home_weighted - road_weighted
    e_point_diff = net_diff * 100
    home_e_points = avg['PTS'].iloc[0] + (e_point_diff / 2)
    road_e_points = avg['PTS'].iloc[0] - (e_point_diff / 2)
    home_WPCT = (home_e_points **13.91) / ((home_e_points **13.91) + (road_e_points **13.91))
    return (home_WPCT * 100), home_e_points, road_e_points


if __name__ == '__main__':
    home = input("Enter Home Team: ")
    road = input("Enter Road Team: ")

    home_id, home_abb = get_team_id(home)
    road_id, road_abb = get_team_id(road)

    home_stats = get_team_stats(home_id, 'Home')
    road_stats = get_team_stats(road_id, 'Road')
    avg_stats = get_league_avg_stats()

    home_WPCT, home_score, road_score = get_win_probabilities(home_stats, road_stats, avg_stats)
    road_WPCT = 100 - home_WPCT

    print(f'Projected Final Score: {home_abb} {home_score}-{road_score} {road_abb}')
    print(f'Projected Win Probability: {home_abb} {home_WPCT}-{road_WPCT} {road_abb}')