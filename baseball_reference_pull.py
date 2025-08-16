# Pull all pitchers' height and weight from Baseball Reference
# Note: need to use vpn to avoid HTTP 429 error

import pandas as pd
import time

teams = [
    "ARI", "ATL", "BAL", "BOS", "CHC", "CHW", "CIN", "CLE",
    "COL", "DET", "HOU", "KCR", "LAA", "LAD", "MIA", "MIL",
    "MIN", "NYM", "NYY", "OAK", "PHI", "PIT", "SDP", "SEA",
    "SFG", "STL", "TBR", "TEX", "TOR", "WSN"
]
year = 2025

pitchers = None

for team in teams:
    url = f"https://www.baseball-reference.com/teams/{team}/{year}-roster.shtml"
    tables = pd.read_html(url)
    roster = tables[0]
    team_pitchers = roster[roster['Unnamed: 4'] == 'Pitcher'][['Name', 'Ht', 'Wt']]
    pitchers = team_pitchers if pitchers is None else pd.concat([pitchers, team_pitchers], ignore_index=True)

# Keep Name, Height, Weight
print(pitchers)
pitchers.to_csv("pitchers_br.csv")