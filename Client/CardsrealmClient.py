import datetime
import time
from datetime import timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from comon_tools.tools import *


class CardsrealmSettings:
    ROOT_URL: str = "https://mtg.cardsrealm.com"
    TOURNAMENT_LIST_URL: str = "https://mtg.cardsrealm.com/en-us/tournament/searchtours"
    DECK_PAGE_URL = "https://mtg.cardsrealm.com/en-us/decks/{deck_id}"
    DECKLIST_JSON_URL: str = "https://mtg.cardsrealm.com/en-us/app/getDeckById"
    ROUND_JSON_URL: str = "https://mtg.cardsrealm.com/en-us/tournament/getround"
    DELAY: int = 2
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0)"
            "Gecko/20100101 Firefox/146.0"
        )
    }
    VALID_FORMATS = ["Pauper"]


class CardsrealmClient:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.session = requests.Session()
        self.session.headers.update(CardsrealmSettings.HEADERS)

    def get_tournaments(self, start_date: datetime, end_date: datetime = None) -> List[Tournament]:
        """Get tournament list with main data"""

        if end_date is None:
            end_date = datetime.now()

        tournaments = []
        page = 1
        last_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Retrieve all tournaments matching the dates
        while last_date >= start_date.strftime("%Y-%m-%d"):
            r = self.session.get(
                CardsrealmSettings.TOURNAMENT_LIST_URL,
                params={
                    "tour_time_select": 3,
                    "tour_region": 0,
                    "tour_name": None,
                    "tour_format": 5,
                    "page": page
                }
            )
            html = json.loads(r.text)
            tournaments_soup = BeautifulSoup(html, "html.parser")

            for tournament_node in tournaments_soup.select("a.tour_grid_banner_a"):
                date_str = tournament_node.select_one(".tour_datetime_utc_p").text.strip()
                last_date = date_str

                if not (start_date.strftime("%Y-%m-%dT00:00:00") <= date_str <= end_date.strftime("%Y-%m-%dT23:59:59")):
                    continue

                tournament = self.extract_tournament_data(tournament_node)
                tournaments.append(tournament)

            page += 1
            time.sleep(CardsrealmSettings.DELAY)

        return tournaments

    def extract_tournament_data(self, tournament_node: Tag) -> Tournament:
        name = tournament_node.select_one(".tour_select_div_name").text.strip()
        date_str = tournament_node.select_one(".tour_datetime_utc_p").text.strip()
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        formats = tournament_node.select_one(".tour_select_div_format_p").text.strip()
        url = urljoin(CardsrealmSettings.ROOT_URL, tournament_node["href"])

        return Tournament(
            name=name,
            date=date,
            uri=url,
            formats=formats if formats in CardsrealmSettings.VALID_FORMATS else None,
            json_file=f"{self.slugify(name)}-{date.strftime('%Y-%m-%d')}.json",
            force_redownload=False
        )

    def scrape_tournament(self, tournament: Tournament) -> Optional[CacheItem]:
        r = self.session.get(tournament.uri)
        html = r.text
        tournament_soup = BeautifulSoup(html, "html.parser")

        # Retrieving decks
        standings = []
        decks = []
        for idx, div in enumerate(tournament_soup.select("div#tour_div_standings div.tour_table_div")):
            if idx == 0:
                continue

            btn = div.select_one("button.decks")
            if not btn:
                continue

            player = div.select_one('p:nth-of-type(2) a[href^="/en-us/leagues/player"]').text.strip()
            rank = int(div.select_one("p:nth-of-type(1)").text.strip())
            points = int(div.select_one("p:nth-of-type(3)").text.strip())
            score = div.select_one("p:nth-of-type(4)").text.strip()
            wins, losses, draws = score.split('-')
            wins = int(wins)
            losses = int(losses)
            draws = int(draws)
            omwp = float(div.select_one("p:nth-of-type(5)").text.strip()) / 100
            gwp = float(div.select_one("p:nth-of-type(6)").text.strip()) / 100
            ogwp = float(div.select_one("p:nth-of-type(7)").text.strip()) / 100
            deck_class_id = btn["id"]

            standing = Standing(
                rank=rank,
                player=player,
                points=points,
                wins=wins,
                losses=losses,
                draws=draws,
                omwp=omwp,
                gwp=gwp,
                ogwp=ogwp
            )

            standings.append(standing)

            div_id = tournament_soup.select_one(
                f'div#tour_div_standings div.{deck_class_id}'
            )["id"]
            deck_id = div_id[5:]
            # print("Deck " + deck_id)

            deck = self.scrape_deck(deck_id, player, rank)
            decks.append(deck)

            time.sleep(CardsrealmSettings.DELAY)

        tour_id = re.search(r'var\s+tour_id\s*=\s*"(\d+)"', html)
        round_count = re.search(r'var\s+tour_round_number\s*=\s*(\d+)', html)

        if not tour_id or not round_count:
            print("No tournament ID or round count. Skip.")
            return None

        tournament_id = tour_id.group(1)
        tournament_round_count = int(round_count.group(1))

        rounds = self.scrape_rounds(tournament_round_count, tournament_id)

        return CacheItem(
            tournament=tournament,
            decks=decks,
            rounds=rounds,
            standings=standings
        )

    def scrape_deck(self, deck_id: str, player: str, rank: int) -> Deck:
        r = self.session.get(
            CardsrealmSettings.DECKLIST_JSON_URL,
            params={"deck_id": deck_id}
        )
        decklist = json.loads(r.text)

        deck = Deck(
            player=player,
            date=None,
            anchor_uri="",
            mainboard=[],
            sideboard=[],
            result=self.format_result(rank)
        )

        for card in decklist:
            deck.anchor_uri = CardsrealmSettings.DECK_PAGE_URL.format(
                deck_id=card["deck_path"]
            )

            target = (
                deck.mainboard
                if card["deck_sideboard"] == 0
                else deck.sideboard
            )

            target.append(DeckItem(
                card_name=card["name_of_card"],
                count=card["deck_quantity"]
            ))

        return deck

    def scrape_rounds(self, round_count: int, tournament_id: str) -> List[Round]:
        rounds = []

        for i in range(1, round_count + 1):
            # print("Round " + str(i))

            r = self.session.get(
                CardsrealmSettings.ROUND_JSON_URL,
                params={"tour_id": tournament_id, "round_number": i}
            )
            round_html = json.loads(r.text)
            round_soup = BeautifulSoup(round_html, "html.parser")

            round = Round(
                round_name="Round " + str(i),
                matches=[]
            )

            for idx, div in enumerate(round_soup.select("div.tour_table_div_round")):
                if idx == 0:
                    continue

                match = self.extract_match(div)
                round.matches.append(match)

            # We don't add empty rounds
            if round.matches:
                rounds.append(round)

            time.sleep(CardsrealmSettings.DELAY)

        return rounds

    @staticmethod
    def extract_match(node: Tag) -> RoundItem:
        player2_node = node.select_one("p:nth-of-type(5) a")
        if player2_node:
            player2 = player2_node.text.strip()
        else:
            player2 = "-"

        player2_score_node = node.select_one("p.tour_results_p:nth-of-type(4)")
        if player2_score_node:
            player2_score = player2_score_node.text.strip()
        else:
            player2_score = 0

        player1 = node.select_one("p:nth-of-type(1) a").text.strip()
        player1_score = node.select_one("p.tour_results_p:nth-of-type(2)").text.strip()
        draws = node.select_one("p.tour_results_p:nth-of-type(3)").text.strip()

        return RoundItem(
            player1=player1,
            player2=player2,
            result=player1_score + "-" + player2_score + "-" + draws,
        )

    @staticmethod
    def slugify(text) -> str:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = re.sub(r'-+', '-', text)
        return text.strip('-')

    @staticmethod
    def format_platform(platform) -> str:
        return {
            "MTGO": "mtgo",
            "SpellTable": "spelltable",
            "Arena": "arena",
        }.get(platform, "paper")

    @staticmethod
    def format_result(rank) -> str:
        if rank == 1:
            return "1st Place"
        if rank == 2:
            return "2nd Place"
        if rank == 3:
            return "3rd Place"
        return f"{rank}th Place"


class TournamentList:
    @classmethod
    def DL_tournaments(cls, start_date: datetime, end_date: datetime = None) -> List[Tournament]:
        """Client entry

        Scrape tournaments on Cards Realm website between start_date and end_date.
        """

        if start_date < datetime(2020, 1, 1, tzinfo=timezone.utc):
            print(f"\r[Cardsrealm] Downloading tournaments before 2020 is not allowed.")
            return []

        if end_date is None:
            end_date = datetime.now(timezone.utc)

        print(
            f"\r[Cardsrealm] Downloading tournaments from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        client = CardsrealmClient(project_dir=Path.cwd())
        result = client.get_tournaments(start_date, end_date)

        return result

    def get_tournament_details(self, tournament: Tournament) -> Optional[CacheItem]:
        """
        Get players, decks, standings and rounds
        """
        client = CardsrealmClient(project_dir=Path.cwd())
        result = client.scrape_tournament(tournament)

        return result
