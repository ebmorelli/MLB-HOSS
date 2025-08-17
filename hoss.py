## Script to calculate Hoss seasons

from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
import pybaseball
import logging
import requests
from io import StringIO
import unicodedata

load_dotenv()  # get environment variables from .env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

hoss_year = int(os.getenv("HOSS_YEAR"))

def height_to_inches(height_str):
    """Helper function to convert <ft><in> height format to just inches"""
    if "-" in height_str:
        feet, inches = height_str.split("-")
    else:
        feet, inches = height_str.split("'")
        inches = inches.replace('"', '').strip()
    return int(feet) * 12 + int(inches)


def remove_accents(text):
    """Helper function to strip accents from names"""
    text = text.encode("latin1").decode("utf-8", errors="ignore")
    if isinstance(text, str):
        return ''.join(
            c for c in unicodedata.normalize('NFKD', text)
            if not unicodedata.combining(c)
        )
    return text

def pull_data_bref() -> pd.DataFrame:
    """
    Pull all pitchers' height and weight from Baseball Reference
    Note: need to use vpn to avoid HTTP 429 error
    """

    if not f"pitchers_bref_{hoss_year}.csv" in os.listdir("pitcher_data"): # data already pulled
        logging.info(f"Pulling {hoss_year} data from Baseball Reference")
        teams = pybaseball.team_batting(hoss_year)["Team"].unique().tolist()
        pitchers = None
        for team in teams:
            url = f"https://www.baseball-reference.com/teams/{team}/{hoss_year}-roster.shtml"
            html = requests.get(url).text
            # Baseball Reference hides most tables inside comments, so strip them out
            clean_html = html.replace("<!--", "").replace("-->", "")
            tables = pd.read_html(StringIO(clean_html))
            roster = tables[0]
            if hoss_year < 2025:
                team_pitchers = roster[roster["P"] > 10][['Player', 'Ht', 'Wt']]
                team_pitchers.rename(columns={"Player": "Name"}, inplace=True)
            else:
                team_pitchers = roster[roster['Unnamed: 4'] == 'Pitcher'][['Name', 'Ht', 'Wt']]
            pitchers = team_pitchers if pitchers is None else pd.concat([pitchers, team_pitchers], ignore_index=True)

        pitchers["Name"] = pitchers["Name"].apply(remove_accents)
        pitchers.to_csv(f"pitcher_data/pitchers_bref_{hoss_year}.csv")
    
    pitchers = pd.read_csv(f"pitcher_data/pitchers_bref_{hoss_year}.csv")
    # Transform data and calculate BMI
    pitchers['height_inches'] = pitchers['Ht'].apply(height_to_inches).apply(int)
    pitchers["Wt"].apply(int)
    pitchers["BMI"] = pitchers["Wt"] / (pitchers["height_inches"])**2
    pitchers["BMI_z"] = (pitchers["BMI"] - pitchers["BMI"].mean()) / pitchers["BMI"].std()

    return pitchers


def pull_data_fg() -> pd.DataFrame:
    """
    Pull pitchers' stats from FanGraphs
    """

    if f"pitchers_fg_{hoss_year}.csv" in os.listdir("pitcher_data"): # data already pulled
        pitching_stats = pd.read_csv(f"pitcher_data/pitchers_fg_{hoss_year}.csv")
    else:
        logging.info(f"Pulling {hoss_year} data from FanGraphs")
        # only pulling stats that I think can be relative to HOSS score
        stat_columns = ["Name", "WAR", "G", "GS", "SO", "K/9", "FIP", "K%", "FB% 2", "FBv", "CTv", "Zone%", "SwStr%", "Stuff+", "Pitching+"]

        pitching_stats = pybaseball.pitching_stats(
            start_season=hoss_year,
            end_season=hoss_year,
        ) # default qual parameter means only qualifying pitchers' data is pulled

        pitching_stats = pitching_stats[stat_columns]
        pitching_stats.to_csv(f"pitcher_data/pitchers_fg_{hoss_year}.csv")
    
    # Transform data and calculate Fastball Velo z-score and WAR z-score
    pitching_stats["fb_velo"] = pitching_stats[["FBv", "CTv"]].max(axis=1, skipna=True)
    pitching_stats['fbv_z'] = (pitching_stats['fb_velo'] - pitching_stats['fb_velo'].mean()) / pitching_stats['fb_velo'].std()
    pitching_stats["WAR_z"] = (pitching_stats["WAR"] - pitching_stats["WAR"].mean()) / pitching_stats["WAR"].std()

    return pitching_stats
    

def main():
    pitchers_bref = pull_data_bref()
    pitchers_fg = pull_data_fg()

    logging.info(f"Calculating HOSS for {hoss_year}")
    pitchers_hoss = pd.merge(
        pitchers_bref, 
        pitchers_fg, 
        on="Name",
        how="left"
    )

    pitchers_hoss["HOSS"] = pitchers_hoss["BMI_z"] + pitchers_hoss["WAR_z"] + pitchers_hoss["fbv_z"]

    pitchers_hoss["HOSS_status"] = (pitchers_hoss["BMI_z"] > 1) & (pitchers_hoss["WAR_z"] > 1) & (pitchers_hoss["fbv_z"] > 1) | (pitchers_hoss["HOSS"] > 6)
    pitchers_sorted = pitchers_hoss.sort_values(by='HOSS', ascending=False)
    pitchers_sorted.to_csv(f"pitcher_data/pitchers_hoss_{hoss_year}.csv")
    print(pitchers_sorted[["Name", "BMI_z", "WAR_z", "fbv_z", "HOSS", "HOSS_status"]].head(10))

if __name__ == "__main__":
    main()
    # for i in range(2025, 2001, -1):
    #     hoss_year = i
    #     main()