import time
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import element_to_be_clickable, invisibility_of_element, visibility_of

from collections import defaultdict
from datetime import datetime
import pickle as pkl
import json
from pathlib import Path
import os

NDV_URL = "https://ndv.2k-dart-software.de/index.php/de/component/dartliga/index.php?option=com_dartliga&controller=showligagameplan&layout=showdashboard&filVbKey=6&filCompKey=1&filSaiKey=112&filVbsubKey=1&filStaffKey=667&filStaffFsGrpdataKey=0#"

class Crawler():

    def __enter__(self):
        options = Options()
        # options.add_argument("--headless")
        self.browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
        self.browser.implicitly_wait(5)
        self.browser.get(NDV_URL)
        self.browser.execute_script("window.loadWaitTime = 10000 * 1000000;")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # self.browser.quit()
        pass
    
    @property
    def page_content(self):
        return BeautifulSoup(self.browser.page_source, "html.parser")

    def refresh(self):
        self.browser.execute_script("window.location.reload();")
        time.sleep(1)
        self.browser.execute_script("window.loadWaitTime = 10000 * 1000000;")

    def wait(self):
        self.browser.implicitly_wait(2)

    def _choose_association(self, association):
        dashboard = self.browser.find_element(By.ID, "showligadashDashboard")
        header_rows = dashboard.find_element(By.CLASS_NAME, "well-sm")
        assoc_div, _ = header_rows.find_elements(By.XPATH, "./*")
        assoc_btns = assoc_div.find_elements(By.CLASS_NAME, "btn")
        for button in assoc_btns:
            if button.get_attribute("title") == association:
                break
        button.click()

    def _choose_competition(self, competition):
        dashboard = self.browser.find_element(By.ID, "showligadashDashboard")
        header_rows = dashboard.find_element(By.CLASS_NAME, "well-sm")
        _, comp_div = header_rows.find_elements(By.XPATH, "./*")
        comp_btns = comp_div.find_elements(By.CLASS_NAME, "btn")
        for button in comp_btns:
            if button.get_attribute("title") == competition:
                break
        button.click()

    def _choose_from_dropdown(self, option):
        dropdown = self.browser.find_element(By.ID, "filOnlrepKeyGameplan")
        select = Select(dropdown)
        select.select_by_visible_text(option)

    def _choose_tab(self, tab):
        dash = self.browser.find_element(By.ID, "showligadashDashboard")
        tab_bar = dash.find_element(By.CLASS_NAME, "nav-tabs")
        tabs = tab_bar.find_elements(By.TAG_NAME, "a")
        for t in tabs:
            if t.find_element(By.TAG_NAME, "span").get_attribute("innerHTML").strip() == tab:
                t.click()
                break

    def _get_results_from_overlay(self, match_row):

        try:
            # this is only visible once we have clicked on the first "spielbericht"
            WebDriverWait(self.browser, timeout=1).until(invisibility_of_element(self.browser.find_element(By.CLASS_NAME, "modal-backdrop")))
        except:
            pass

        # crashes when game has not been played yet
        try:
            button = match_row.find_element(By.CLASS_NAME, "ligameplBtnLigameplgameExist")
            button.click()
        except:
            print("Skipping match, no button", match_row.get_attribute("outerHTML"))
            return 

        matches = []

        table = self.browser.find_element(By.ID, "ligameplgame").find_element(By.TAG_NAME, "table")
        match_rows = table.find_elements(By.CLASS_NAME, "resultTable")
        for i, m in enumerate(match_rows):
            match_info = m.find_elements(By.TAG_NAME, "td")
            match = {}
            match["home_player"] = match_info[2].get_attribute("textContent")
            match["result"] = match_info[3].get_attribute("textContent")
            match["away_player"] = match_info[4].get_attribute("textContent")
            if i in [0, 1, 2, 3]:
                match_number = i + 1
            elif i in [6, 7, 8, 9]:
                match_number = i - 5
            elif i in [4, 5]:
                match_number = i - 3
            elif i in [10, 11]:
                match_number = i - 9
            match["match_number"] = match_number
            matches.append(match)

        self._close_match_overlay()
        return matches

    def _close_match_overlay(self):
        dialogue = self.browser.find_element(By.ID, "showligadashDialog")
        button = dialogue.find_element(By.TAG_NAME, "button")
        wait = WebDriverWait(self.browser, timeout=15).until(element_to_be_clickable(button))
        time.sleep(1)
        # self.browser.execute_script("arguments[0].click();", button)
        button.click()

    def get_associations(self):
        dashboard = self.browser.find_element(By.ID, "showligadashDashboard")
        header_rows = dashboard.find_element(By.CLASS_NAME, "well-sm")
        assoc_div, competition_div = header_rows.find_elements(By.XPATH, "./*")

        assoc_elements = assoc_div.find_elements(By.TAG_NAME, "a")
        assocs = [a.get_attribute("title") for a in assoc_elements]
        return assocs

    def get_competitions(self, association):
        self._choose_association(association)
        dashboard = self.browser.find_element(By.ID, "showligadashDashboard")
        header_rows = dashboard.find_element(By.CLASS_NAME, "well-sm")
        _, competition_div = header_rows.find_elements(By.XPATH, "./*")

        comp_elements = competition_div.find_elements(By.TAG_NAME, "a")
        comps = [a.get_attribute("title") for a in comp_elements]
        return comps

    def get_clubs_and_teams(self, associations : list = None, competitions : list = None):
        teams = defaultdict(set) # holds club : {A, B, C, D, E}
        players = [] # {(assoc id, name, club)}

        if associations is None:
            associations = self.get_associations()

        for assoc in associations:
            time.sleep(1)
            self._choose_association(assoc)
            if competitions is None:
                competitions = self.get_competitions(assoc)
            
            for comp in competitions:
                time.sleep(1)
                self._choose_competition(comp)
                time.sleep(1)
                self._choose_tab("Spielerkader")
                time.sleep(1)
                self._choose_association(assoc)
                time.sleep(1)
        
                squad_panel = self.browser.find_element(By.ID, "showPlayerSquadAreaData")
                team_headings = squad_panel.find_elements(By.CLASS_NAME, "panel-heading") #previous "collapsed"

                for team_heading in team_headings:

                    team_id = team_heading.get_attribute("id").replace("teamTopic", "")
                
                    club_team_name = team_heading.get_attribute("textContent").strip()
                    club, team = club_team_name[:-2], club_team_name[-1]
                    club = club.strip()
                    print(f"|{club}|")
                    teams[club].add(team)
                    team_data = squad_panel.find_element(By.ID, f"teamData{team_id}")

                    player_spans = team_data.find_elements(By.CLASS_NAME, "form-control-static")
                    player_info = [p.get_attribute("textContent") for p in player_spans]
                    for p in player_info:
                        player = p.replace("TC", "").strip().split("(")
                        # TODO: Fix player ordering! Currently van Hooff, Jens -> Hooff Jens van
                        # van Hooff, Jens (100405)
                        # ["van Hooff, Jens", 100405)]
                        name_split = player[0].split(",")
                        name = f"{' '.join([n.strip() for n in name_split[1:]])} {name_split[0]}".strip()
                        if "Spieler ist nicht" in name:
                            continue
                        id = player[-1][:-1]
                        print(name)
                        players.append((id, name, club))
        return teams, players

    def get_matches(self, associations : list = None, competitions : list = None, from_date=datetime(2022,8,1)):
        # click on each "Spielbericht" that took place after "from_date"
        # If there is data available, parse into pandas from html table
        # make these fit via match number in table
        matchdays = [] # hold match dicts 
        matches = [] # hold list of single/double matches per matchday

        if associations is None:
            associations = self.get_associations()

        for assoc in associations:
            self._choose_association(assoc)
            if competitions is None:
                competitions = self.get_competitions(assoc)
            
            for comp in competitions:
                time.sleep(1)
                self._choose_competition(comp)
                time.sleep(1)
                self._choose_tab("Spielplan")
                time.sleep(1)
                self._choose_from_dropdown("Spielplan")
                dashboard = self.browser.find_element(By.ID, "showGameplanAreaData")
                matchday_bodys = dashboard.find_elements(By.TAG_NAME, "tbody")
                for matchday in matchday_bodys:
                    match_rows = matchday.find_elements(By.TAG_NAME, "tr")
                    for match_row in match_rows:
                        if len(match_row.get_attribute("id")):
                            continue
                    
                        matchday_info = {}
                        match_info = match_row.find_elements(By.TAG_NAME, "td")
                        date = match_info[0].get_attribute("textContent")
                        if not "." in date:
                            continue
                        _, date, time_ = date.split(" ")
                        d, m, y = date.split(".")
                        h, min = time_.split(":")
                        match_date = datetime(int(y)+2000, int(m), int(d), int(h), int(min))

                        if match_date < from_date:
                            print("skip", match_date, from_date)
                            continue
                        
                        matchday_info["date"] = match_date
                        matchday_info["home_team"] = match_info[1].get_attribute("textContent").strip()
                        matchday_info["away_team"] = match_info[2].get_attribute("textContent").strip()
                        matchday_info["result"] = match_info[3].get_attribute("textContent").strip()
                        matchday_info["legs"] = match_info[4].get_attribute("textContent").strip()
                        matchday_info["competition"] = comp
                        matchday_info["association"] = assoc
                        
                        if not matchday_info["result"].strip() == "-:-":
                            results = self._get_results_from_overlay(match_info[-1])

                            matchdays.append(matchday_info)
                            matches.append(results)
        return matchdays, matches


if "__main__" == __name__:
    import argparse
    parser = argparse.ArgumentParser(
        description='Crawl data from 2k app.'
    )

    parser.add_argument('--date', help="Matches before this date are ignored. Expects YYYY-MM-DD.", required=False)
    parser.add_argument("--path", help="Destination for the crawled data.", required=True)
    parser.add_argument('--season', help="What season we crawl. Expects YYYY (will be set to first of august that year.)", required=True, type=int)
    parser.add_argument("--associations", help="Limit associations to be crawled.", nargs="*", default=["DBH", "NDV"])
    args = parser.parse_args()

    data_path = Path(args.path)
    # os.makedirs(data_path, exist_ok=True)
    if not args.date:
        from_date = datetime(2022, 8, 1)
    else:
        from_date = datetime.fromisoformat(args.date)
    
    season = datetime(args.season, 8, 1)
    print("Only checking matches past", from_date)

    results = {}
    results["from_date"] = from_date.isoformat()
    results["crawled_date"] = datetime.now().isoformat()
    results["season"] = season.isoformat()
    results["crawled_competitions"] = {}
    with Crawler() as crawler:
        if args.associations[0] == "all":
            assocs = crawler.get_associations()
        else:
            assocs = args.associations
        for a in assocs:
            comps = crawler.get_competitions(a)
            results["crawled_competitions"][a] = []
            results[a] = {}
            for comp in comps:
                results["crawled_competitions"][a].append(comp)
                results[a][comp] = {}
                clubs_teams, players = crawler.get_clubs_and_teams([a], [comp])
                matchdays, matches = crawler.get_matches([a], [comp], from_date=from_date)
                results[a][comp]["clubs_teams"] = {club : list(teams) for club, teams in clubs_teams.items()}
                results[a][comp]["matches"] = matches
                results[a][comp]["players"] = players
                for match in matchdays:
                    match["date"] = match["date"].isoformat()
                results[a][comp]["team_matches"] = matchdays

    with open(data_path, "w+") as f:
        json.dump(results, f)
    

    

