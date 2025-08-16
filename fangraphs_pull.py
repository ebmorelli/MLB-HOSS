# Pull all pitchers' stats from FanGraphs

import pybaseball

# only pulling stats that I think can be relative to HOSS score
stat_columns = ["Name", "WAR", "G", "GS", "SO", "K/9", "FIP", "K%", "FB% 2", "vFA (sc)", "vSI (sc)", "vFC (sc)", "Zone%", "SwStr%", "Stuff+", "Pitching+"]

pitching_stats = pybaseball.pitching_stats(
    start_season=2025,
    end_season=2025,
    qual = 30,
)

pitching_stats = pitching_stats[stat_columns]
pitching_stats.to_csv("pitchers_fg.csv")