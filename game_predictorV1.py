from nba_api.stats.static import teams
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
    
team_id = get_team_id("jazz")
print(team_id)