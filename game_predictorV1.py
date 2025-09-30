from nba_api.stats.endpoints import leaguedashteamstats
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