# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta, timezone
import os
import time
# import sys
from typing import List, Optional
# import html
from dataclasses import dataclass
from models.Melee_model import *
from models.base_model import *
from comon_tools.tools import *
from requests.cookies import RequestsCookieJar
# sys.path.append(os.path.abspath(os.path.dirname(__file__)))


class MtgMeleeClient:
    @staticmethod
    def get_client(load_cookies: bool = False):
        """
        Create and configure a requests session for interacting with MTG Melee.
        
        Parameters:
        - load_cookies (bool): If True, attempt to load cookies from file if still valid.
                               Defaults to False.
        
        Returns:
        - session (requests.Session): Configured requests session.
        """
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        })
        if load_cookies:
            # Load cookies if still valid
            cookies_are_valid = MtgMeleeClient._cookies_valid()
            MtgMeleeClient._refresh_cookies(session, force_login=not cookies_are_valid)
            
            if cookies_are_valid:
                MtgMeleeClient._load_cookies(session)
        return session
    
    @staticmethod
    def _cookies_valid():
        if not os.path.exists(MtgMeleeConstants.COOKIE_FILE):
            return False
        try:
            with open(MtgMeleeConstants.COOKIE_FILE, "r") as f:
                data = json.load(f)
                timestamp = data.get("_timestamp")
                if not timestamp:
                    return False
                age = datetime.now() - datetime.fromtimestamp(timestamp)
                return age < timedelta(days=MtgMeleeConstants.COOKIE_MAX_AGE_DAYS)
        except Exception:
            return False

    @staticmethod
    def _load_cookies(session):
        # need to reresh __RequestVerificationToken
        with open(MtgMeleeConstants.COOKIE_FILE, "r") as f:
            data = json.load(f)
            cookies = data.get("cookies", {})
            session.cookies.update(cookies)
    @staticmethod
    def _refresh_cookies(session, force_login=False):
        # Initialiser la session
        session.cookies.clear()

        # Headers classiques pour accéder au formulaire de login
        classic_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://melee.gg/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        # Step 1: GET login page to extract __RequestVerificationToken
        login_page = session.get("https://melee.gg/Account/SignIn", headers=classic_headers)
        if login_page.status_code != 200:
            raise Exception(f"Failed to load login page: {login_page.status_code}")

        soup = BeautifulSoup(login_page.text, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_input:
            raise Exception("CSRF token not found in login page")
        token = token_input["value"]

        if force_login:
            # Load credentials
            if not os.path.exists(MtgMeleeConstants.CRED_FILE):
                raise FileNotFoundError("Missing login file: melee_login.json")
            with open(MtgMeleeConstants.CRED_FILE, "r") as f:
                creds = json.load(f)

            # Prepare AJAX headers and payload
            ajax_headers = {
                "User-Agent": classic_headers["User-Agent"],
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://melee.gg",
                "Referer": "https://melee.gg/Account/SignIn"
            }

            login_payload = {
                "email": creds["login"],
                "password": creds["mdp"],
                "__RequestVerificationToken": token
            }

            # Step 2: POST login
            response = session.post(
                "https://melee.gg/Account/SignInPassword",
                headers=ajax_headers,
                data=login_payload
            )

            if response.status_code != 200 or '"Error":true' in response.text:
                print("Raw response: ", response.text[:1000])
                raise Exception(f"Login failed: status={response.status_code}")

            if ".AspNet.ApplicationCookie" not in session.cookies.get_dict():
                raise Exception(f"Login did not set auth cookie properly: {session.cookies.get_dict()}")

            # Save cookies
            cookies_to_store = {
                "cookies": session.cookies.get_dict(),
                "_timestamp": time.time()
            }
            with open(MtgMeleeConstants.COOKIE_FILE, "w") as f:
                json.dump(cookies_to_store, f, indent=2)

    @staticmethod
    def normalize_spaces(data):
        return re.sub(r'\s+', ' ', data).strip()

    def get_players(self, uri, max_players=None):
        result = []
        # je ne suis pas sur de bien comprendre pourquoi utilisé self ici sachant qu'on appel une méthode static
        # page_content = self.get_client().get(uri).text
        page_content = MtgMeleeClient.get_client().get(uri).text
        soup = BeautifulSoup(page_content, 'html.parser')

        round_nodes = soup.select('button.btn.btn-gray.round-selector[data-is-completed="True"]')

        if not round_nodes:
            return None

        round_ids = [node['data-id'] for node in round_nodes]
        
        has_data = True
        offset = 0
        # debug
        round_id = round_ids[-1]

        while True:
        # has_data and (max_players is None or offset < max_players):
            has_data = False
            round_parameters = MtgMeleeConstants.ROUND_PAGE_PARAMETERS.replace("{start}", str(offset)).replace("{roundId}", round_id) 
            round_url = MtgMeleeConstants.ROUND_PAGE 
            response = MtgMeleeClient.get_client().post(round_url, data=round_parameters)
            # print("Réponse obtenue:", response.status_code)
            round_data = json.loads(response.text)

            if len(round_data['data']) == 0 and offset == 0:
                if len(round_ids) > 1:
                    round_ids = round_ids[:-1]
                    round_id = round_ids[-1]
                    has_data = True
                    continue
                else:
                    break

            for entry in round_data['data']:
                has_data = True
                player_name = entry['Team']['Players'][0]['DisplayName']
                if not player_name:
                    continue

                player_name = self.normalize_spaces(player_name)
                user_name = entry['Team']['Players'][0]['Username']
                player_points = entry['Points']
                omwp = entry['OpponentMatchWinPercentage']
                gwp = entry['TeamGameWinPercentage']
                ogwp = entry['OpponentGameWinPercentage']
                player_position = entry['Rank']
                wins = entry['MatchWins']
                losses = entry['MatchLosses']
                draws = entry['MatchDraws']
                nb_of_oppo = entry['OpponentCount']

                standing = Standing(
                    player=player_name,
                    rank=player_position,
                    points=player_points,
                    omwp=omwp,
                    gwp=gwp,
                    ogwp=ogwp,
                    wins=wins,
                    losses=losses,
                    draws=draws
                )

                player_decks = []
                for decklist in entry['Decklists']:
                    deck_list_id = decklist['DecklistId']
                    if not deck_list_id:
                        continue
                    decklist_format = decklist['Format']
                    player_decks.append(MtgMeleePlayerDeck(
                        deck_id=deck_list_id,
                        format=decklist_format,
                        uri=MtgMeleeConstants.format_url(MtgMeleeConstants.DECK_PAGE, deckId=deck_list_id)
                    ))

                result.append(
                    MtgMeleePlayerInfo( 
                        username=user_name,
                        player_name=player_name,
                        result=f"{wins}-{losses}-{draws}",
                        standing=standing,
                        decks=player_decks if player_decks else None,
                        nb_of_oppo = nb_of_oppo
                )
                )

            offset += 25
            # print(offset)
            if not has_data or (max_players is not None and offset >= max_players):
                break
        return result

    def get_deck(self, uri, players, skip_round_data=False):
        deck_page_content = self.get_client().get(uri).text
        deck_soup = BeautifulSoup(deck_page_content, 'html.parser')


        deck_text = deck_soup.select_one("pre#decklist-text")
        card_list = deck_text.text.split("\r\n")

        player_link_element = deck_soup.select_one("a.text-nowrap.text-muted")

        player_url = player_link_element['href']
        player_raw = player_link_element.select_one("span.text-nowrap").text.strip()

        player_name = self.get_player_name(player_raw, player_url, players)

        date_string = deck_soup.select_one('span[data-toggle="date"]')['data-value'].strip()

        date_tournament = datetime.strptime(date_string, "%m/%d/%Y %I:%M:%S %p")

        format_div = deck_soup.select_one(".d-flex.flex-row.gap-8px .text-nowrap:last-of-type")
        format = format_div.text.strip()

        main_board = []
        side_board = []
        inside_sideboard = inside_companion = inside_commander = False
        CardNameNormalizer.initialize()
        for card in card_list:
            if card in ['MainDeck', 'Companion', 'Sideboard','Commander','']:
                if card == 'Commander':
                    inside_commander = True
                else:
                    inside_companion = card == 'Companion'
                    inside_sideboard = card == 'Sideboard'         
                if(inside_commander):
                    inside_sideboard = True
                if(card == 'Deck' and inside_commander):
                    inside_sideboard = False
                    inside_commander = False
                    inside_companion = False
            else:
                if inside_companion and not inside_commander:
                    continue
                count, name = card.split(" ", 1)
                count = int(count)
                name = CardNameNormalizer.normalize(name)

                if inside_sideboard:
                    side_board.append(DeckItem(card_name=name, count=count))
                else:
                    main_board.append(DeckItem(card_name=name, count=count))
        rounds = []
        if not skip_round_data:
            # Extract the decklist GUID from the URI
            decklist_guid = uri.split('/')[-1]

            # Construct the API endpoint URL
            api_url = f"https://melee.gg/Decklist/GetTournamentViewData/{decklist_guid}"

            try:
                # Make the API request
                response = self.get_client().get(api_url)
                if response.status_code == 200:
                    match_data = response.json()

                    # Parse the nested JSON string in the 'Json' key
                    if 'Json' in match_data and match_data['Json']:
                        inner_data = json.loads(match_data['Json'])

                        # Now check for 'Matches' in the parsed inner data
                        if 'Matches' in inner_data and inner_data['Matches']:
                            for match in inner_data['Matches']:
                                round_name = f"Round {match['Round']}"
                                opponent_name = match['Opponent'] if match['Opponent'] else "-"
                                result = match['Result']

                                # Use the existing get_round method with adapted parameters
                                round_info = self.get_round_from_api(round_name, player_name, opponent_name, result)
                                if round_info:
                                    rounds.append(round_info)
            except Exception as e:
                print(f"Error fetching match data from API: {e}")

        return MtgMeleeDeckInfo(
            # in order to match badaro test put date to none,
            # date=date = date_tournament, 
            date=None,
            deck_uri=uri,
            player=player_name,
            format=format,
            mainboard=main_board,
            sideboard=side_board,
            rounds=rounds if rounds else None
        )

    def get_round_from_api(self, round_name, player_name, opponent_name, result):
        """Parse round information from API data"""
        item = None
        if result.startswith(f"{player_name} won"):
            item = RoundItem(player1=player_name, player2=opponent_name, result=result.split(" ")[-1])
        elif opponent_name != "-" and result.startswith(f"{opponent_name} won"):
            item = RoundItem(player1=opponent_name, player2=player_name, result=result.split(" ")[-1])
        elif "Draw" in result:
            item = RoundItem(player1=player_name, player2=opponent_name, result=result.split(" ")[0])
        elif "bye" in result or "was awarded a bye" in result:
            item = RoundItem(player1=player_name, player2="-", result="2-0-0")
        elif result.startswith("won "):
            item = RoundItem(player1="-", player2=player_name, result="2-0-0")
        elif result.startswith(f"{player_name} forfeited"):
            item = RoundItem(player1=player_name, player2=opponent_name, result="0-2-0")
        elif result.startswith("Not reported") or "[FORMAT EXCEPTION]" in result:
            item = RoundItem(player1=player_name, player2=opponent_name, result="0-0-0")
        elif f"{player_name} forfeited" in result and f"{opponent_name} forfeited" in result:
            item = RoundItem(player1=player_name, player2=opponent_name, result="0-0-0")
        if item is None:
            raise ValueError(f"Cannot parse round data for player {player_name} and opponent {opponent_name}")

        if len(item.result.split("-")) == 2:
            item.result += "-0"

        return MtgMeleeRoundInfo(round_name=round_name, match=item)

    def get_round(self, round_node, player_name, players):
        """Legacy method for HTML parsing - kept for compatibility"""
        round_columns = round_node.find_all("td")
        if len(round_columns) < 4:  # Make sure there are enough columns
            return None

        if "No matches available" in round_node.text:
            return None

        round_name = f"Round {self.normalize_spaces(round_columns[0].text.strip())}"

        a_tag = round_columns[1].find("a")
        round_opponent_url = a_tag.get("href", "") if a_tag else ""
        round_opponent_raw = a_tag.text if a_tag else ""
        round_opponent = self.get_player_name(round_opponent_raw, round_opponent_url, players) if round_opponent_raw else "-"

        round_result = self.normalize_spaces(round_columns[3].text.strip())

        return self.get_round_from_api(round_name, player_name, round_opponent, round_result)

    def get_player_name(self, player_name_raw, profile_url, players):
        player_id = profile_url.split("/")[-1]
        # p = players[0]
        # p.username
        if player_id:
            player_info = next((p for p in players if p.username == player_id), None)
            if player_info:
                return player_info.player_name
            elif player_name_raw:
                return self.normalize_spaces(player_name_raw)
        return "-"
    
    def get_tournaments(self, start_date, end_date):
        length_tournament_page = 1000
        result = []
        draw = 1
        Tournament_resutl = []

        while True:
            payload = MtgMeleeConstants.build_magic_payload(start_date, end_date, length=length_tournament_page,draw = draw,start = 0)
            tournament_list_url = 'https://melee.gg/Decklist/SearchDecklists' # MtgMeleeConstants.TOURNAMENT_LIST_PAGE
            response = self.get_client(load_cookies = True).post(tournament_list_url,data=payload)
            tournament_data = json.loads(response.text)
            
            result.extend(tournament_data.get("data", []))
            if tournament_data["recordsFiltered"] < 1000:
                break
            draw += 1
        # Group all data by tournament
        tournaments = {}
        # Iterate over each player record in the result list
        for item in result:
            tournament_id = item['TournamentId']
            
            # If the tournament has not been added yet, initialize it
            if tournament_id not in tournaments:
                tournments_url_loop = MtgMeleeConstants.TOURNAMENT_PAGE.replace("{tournamentId}", str(tournament_id))
                tournament_page = self.get_client().get(tournments_url_loop).text

                # Parser le HTML
                soup = BeautifulSoup(tournament_page, "html.parser")

                # Chercher le bloc où est écrit l'info
                registration_info = soup.find("p", id="tournament-headline-registration")
                text = registration_info.get_text()
                # Utiliser une regex pour extraire ce qui suit "Format: " jusqu'à " |"
                match = re.search(r'Format: (.*?) \|', text)
                if match:
                    tournament_format = match.group(1)
                tournaments[tournament_id] = {
                    'players': {},  # player_name -> decklist
                    'date': datetime.strptime(item['TournamentStartDate'], "%Y-%m-%dT%H:%M:%S"),
                    'name': item.get('TournamentName', 'Unnamed Tournament'),
                    'organizer': item['OrganizationName'],
                    'formats': tournament_format,# item.get('FormatDescription'),
                    'uri': MtgMeleeConstants.TOURNAMENT_PAGE.replace("{tournamentId}", str(tournament_id)),
                    'statut': str(item['TournamentStatusDescription']),  # You can convert this to a label later
                }

            # Add player decklist
            player_name = item.get('OwnerUsername')  or "UnknownPlayer" #or item.get('DiscordUsername') or 
            tournaments[tournament_id]['players'][player_name] =  melee_extract_decklist(
                date = datetime.strptime(item['TournamentStartDate'], "%Y-%m-%dT%H:%M:%S"),
                TournamentId =  tournament_id,
                Valid = item.get('IsValid'),
                OwnerDisplayName =  item.get('OwnerDisplayName'),
                OwnerUsername = item.get('OwnerUsername') or "UnknownPlayer",
                Guid = item.get('Guid'),
                DecklistName = item.get('DecklistName'),
                decklists = item['Records'],
                decklists_formats = item.get('FormatDescription')
            )

        # Convert the structured dictionary to a list of MtgMeleeTournamentInfo objects
        tournament_infos = []

        for tournament_id, data in tournaments.items():
            tournament_info = MtgMeleeTournamentInfo(
                tournament_id=tournament_id,
                uri=data['uri'],
                date=data['date'],
                organizer=data['organizer'],
                name=data['name'],
                decklists=data['players'],
                formats=data['formats'],
                statut=data['statut'],
            )
            tournament_infos.append(tournament_info)

        return tournament_infos
    


# Configuration settings
class MtgMeleeAnalyzerSettings:
    ValidFormats = ["Standard", "Modern", "Pioneer", "Legacy", "Vintage", "Pauper","Commander","Premodern"] #
    PlayersLoadedForAnalysis = 25
    DecksLoadedForAnalysis = 16
    BlacklistedTerms = ["Team "]


class MtgMeleeAnalyzer:
    _banned_only_in_duel = None  # cache shared across all instances
    @classmethod
    def _get_banned_only_in_duel(cls):
        """Fetch and cache the list of cards banned in Duel Commander but not in multiplayer Commander."""
        if cls._banned_only_in_duel is None:
            def get_banned_cards(format_name):
                url = f"https://api.scryfall.com/cards/search"
                params = {
                    "q": f"banned:{format_name}",
                    "unique": "cards"
                }
                cards = []
                while url:
                    response = requests.get(url, params=params if url.endswith('/search') else None)
                    data = response.json()
                    cards.extend(data["data"])
                    url = data.get("next_page")
                return set(card["name"] for card in cards)

            banned_duel = get_banned_cards("duel")
            banned_multi = get_banned_cards("commander")
            cls._banned_only_in_duel = banned_duel - banned_multi
        return cls._banned_only_in_duel
    
    def get_scraper_tournaments(self, tournament: MtgMeleeTournamentInfo) -> Optional[List[MtgMeleeTournament]]:
        is_pro_tour = (
            tournament.organizer == "Wizards of the Coast" and
            ("Pro Tour" in tournament.name or "World Championship" in tournament.name) and
            "Qualifier" not in tournament.name
        )
        # Skips tournaments with blacklisted terms
        if any(term.lower() in tournament.name.lower() for term in MtgMeleeAnalyzerSettings.BlacklistedTerms):
            return None

        # Skips tournaments with weird formats
        if not is_pro_tour and any(f not in MtgMeleeAnalyzerSettings.ValidFormats for f in tournament.formats):
            return None
        # skip not ended tournament 'In Progress'
        if tournament.statut != 'Ended' and (tournament.date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)) < timedelta(days=5):
            return None
        
        client = MtgMeleeClient()
        players = client.get_players(tournament.uri, MtgMeleeAnalyzerSettings.PlayersLoadedForAnalysis)
        # Skips empty tournaments
        if not players:
            return None
        # Not commander multi tournament

        if any(f == 'Commander' for f in tournament.formats):
            # Access the banned list only once, when needed
            banned_cards = self._get_banned_only_in_duel()
            for player in players:
                if player.nb_of_oppo >  (player.standing.wins + player.standing.losses + player.standing.draws):
                    return None
                

        max_decks_per_player = max((len(p.decks) for p in players if p.decks), default=0)

        if is_pro_tour:
            return [self.generate_pro_tour_tournament(tournament, players)]
        else:
            if max_decks_per_player == 1:
                return [self.generate_single_format_tournament(tournament)]
            else:
                result = []
                for i in range(max_decks_per_player):
                    result.append(self.generate_multi_format_tournament(tournament, players, i, max_decks_per_player))
                return result

    def generate_single_format_tournament(self, tournament: MtgMeleeTournamentInfo) -> MtgMeleeTournament:
        format_detected = tournament.formats[0]
        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            formats=format_detected,
            json_file=self.generate_file_name(tournament, format_detected, -1)
        )

    def generate_multi_format_tournament(self, tournament: MtgMeleeTournamentInfo, players: List[MtgMeleePlayerInfo], offset: int, expected_decks: int) -> MtgMeleeTournament:
        deck_uris = [
            p.decks[offset].uri for p in players if p.decks and len(p.decks) > offset
        ][:MtgMeleeAnalyzerSettings.DecksLoadedForAnalysis]

        decks = [MtgMeleeClient().get_deck(uri, players, True) for uri in deck_uris]
        formats = {deck.format for deck in decks}  # Ensemble des formats uniques

        if len(formats) > 1:
            raise ValueError(f"multiple formats need fix : {formats}")
        # format_detected = FormatDetector.detect(decks)
        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            formats=formats.pop(),
            json_file=FilenameGenerator.generate_file_name(
                tournament_id=tournament.uri.split("/")[-1],
                name=tournament.name,
                date=tournament.date,
                format=formats.pop(),
                valid_formats=MtgMeleeAnalyzerSettings.ValidFormats,
                offset=offset
            ),
            deck_offset=offset,
            expected_decks=expected_decks,
            fix_behavior="Skip"
        )

    def generate_pro_tour_tournament(self, tournament: MtgMeleeTournamentInfo, players: List[MtgMeleePlayerInfo]) -> MtgMeleeTournament:
        deck_uris = [p.decks[-1].uri for p in players if p.decks]
        decks = [MtgMeleeClient().get_deck(uri, players, True) for uri in deck_uris]

        formats = {deck.format for deck in decks}  

        if len(formats) > 1:
            raise ValueError(f"multiple formats need fix  : {formats}")
        format_detected = formats.pop()
        # format_detected = FormatDetector.detect(decks)
        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            formats=format_detected,
            json_file=self.generate_file_name(tournament, format_detected, -1),
            deck_offset=0,
            expected_decks=3,
            fix_behavior="UseFirst",
            excluded_rounds=["Round 1", "Round 2", "Round 3", "Round 9", "Round 10", "Round 11"]
        )

    def generate_file_name(self, tournament: MtgMeleeTournamentInfo, format: str, offset: int) -> str:
        name = tournament.name
        if format.lower() not in name.lower():
            name += f" ({format})"

        for other_format in MtgMeleeAnalyzerSettings.ValidFormats:
            if other_format.lower() != format.lower() and other_format.lower() in name.lower():
                name = name.replace(other_format, other_format[:3], 1)

        if offset >= 0:
            name += f" (Seat {offset + 1})"

        return f"{SlugGenerator.generate_slug(name.strip())}-{tournament.uri.split('/')[-1]}-{tournament.date.strftime('%Y-%m-%d')}.json"


class TournamentList:
    def get_tournament_details(self,  tournament: MtgMeleeTournament) -> 'CacheItem':
        client = MtgMeleeClient()
        players = client.get_players(tournament.uri)
        
        decks = []
        standings = []
        consolidated_rounds = {}
        current_position = 1
        # player = players[0]
        # uri = tournament.uri
        for player in players:
            standings.append(player.standing)
            player_position = player.standing.rank
            player_result = f"{player_position}th Place" if player_position > 3 else f"{player_position}st Place"  # Simplified result naming

            if len(player.decks) > 0:
                deck_uri = player.decks[-1].uri
                deck = MtgMeleeClient().get_deck(deck_uri, players)
            else: 
                deck = None
            if deck is not None:
                decks.append(
                    MtgMeleeDeckInfo(
                    # in order to match badaro test put date to none,
                    # date=tournament.date, 
                    date=None,
                    deck_uri=deck.deck_uri,
                    player=player.player_name,
                    format= deck.format,
                    mainboard=deck.mainboard,
                    sideboard=deck.sideboard,
                    result =player_result,
                    rounds=deck.rounds
                )
                )

            # Consolidating rounds
            if deck is not None and deck.rounds:
                deck_round = deck.rounds[0]
                for deck_round in deck.rounds:
                    if tournament.excluded_rounds is not None and deck_round.round_name in tournament.excluded_rounds:
                        continue

                    if deck_round.round_name not in consolidated_rounds:
                        consolidated_rounds[deck_round.round_name] = {}

                    round_item_key = f"{deck_round.round_name}_{deck_round.match.player1}_{deck_round.match.player2}"
                    if round_item_key not in consolidated_rounds[deck_round.round_name]:
                        consolidated_rounds[deck_round.round_name][round_item_key] = deck_round.match        
        rounds = [Round(round_name, list(matches.values())) for round_name, matches in consolidated_rounds.items()]
        
        return CacheItem(
            tournament=tournament,
            decks=decks,
            standings=standings,
            rounds=rounds
        )

    @classmethod
    def DL_tournaments(cls,start_date: datetime, end_date: datetime = None) -> List[dict]:
        """Récupérer les tournois entre les dates start_date et end_date."""
        if start_date < datetime(2020, 1, 1, tzinfo=timezone.utc):
            return []  # Si la date de départ est avant le 1er janvier 2020, retourner une liste vide.
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        result = []
        while start_date < end_date:
            current_end_date = start_date + timedelta(days=7)
            print(f"\r[MtgMelee] Downloading tournaments from {start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}", end="")
            # Créer une instance du client et récupérer les tournois
            client = MtgMeleeClient()
            tournaments = client.get_tournaments(start_date, current_end_date)
            analyzer = MtgMeleeAnalyzer()
            for tournament in tournaments:
                melee_tournaments = analyzer.get_scraper_tournaments(tournament)
                if melee_tournaments:
                    result.extend(melee_tournaments)
            start_date = current_end_date
        print("\r[MtgMelee] Download finished".ljust(80))
        return result




#############################################################################################

