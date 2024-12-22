# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:39:50 2024

@author: Francois
"""
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass



@dataclass
class Tournament:
    def __init__(self, date: datetime, name: str, uri: str, json_file: Optional[str] = None, force_redownload: bool = False):
        self.date = date
        self.name = name
        self.uri = uri
        self.json_file = json_file
        self.force_redownload = force_redownload

    def __str__(self):
        return f"{self.name}|{self.date.strftime('%Y-%m-%d')}"

@dataclass
class Standing:
    def __init__(self, rank: int, player: str, points: int, wins: int, losses: int, draws: int, omwp: float, gwp: float, ogwp: float):
        self.rank = rank
        self.player = player
        self.points = points
        self.wins = wins
        self.losses = losses
        self.draws = draws
        self.omwp = omwp
        self.gwp = gwp
        self.ogwp = ogwp

    def __str__(self):
        return f"#{self.rank} {self.player} {self.points} points"

@dataclass
class RoundItem:
    def __init__(self, player1: str, player2: str, result: str):
        self.player1 = player1
        self.player2 = player2
        self.result = result

    def __str__(self):
        return f"{self.player1} {self.result} {self.player2}"

@dataclass
class Round:
    def __init__(self, round_name: str, matches: List[RoundItem]):
        self.round_name = round_name
        self.matches = matches

    def __str__(self):
        return f"Round: {self.round_name}, {len(self.matches)} matches"

@dataclass
class DeckItem:
    def __init__(self, count: int, card_name: str):
        self.count = count
        self.card_name = card_name
    def __str__(self):
        return f"count : {self.count}, card name : {self.card_name}"
    def __eq__(self, other):
        if isinstance(other, DeckItem):
            return self.count == other.count and self.card_name == other.card_name
        return False
@dataclass
class Deck:
    def __init__(self, date: Optional[datetime], player: str, result: str, anchor_uri: str,
                 mainboard: List[DeckItem], sideboard: List[DeckItem]):
        self.date = date
        self.player = player
        self.result = result
        self.anchor_uri = anchor_uri
        self.mainboard = mainboard
        self.sideboard = sideboard

    def contains(self, *cards: str) -> bool:
        return all(any(item.card_name == c for item in self.mainboard) or 
                   any(item.card_name == c for item in self.sideboard) for c in cards)

    def __str__(self):
        total = sum(item.count for item in self.mainboard) + sum(item.count for item in self.sideboard)
        return f"{total} cards"

@dataclass
class CacheItem:
    def __init__(self, tournament: Tournament, decks: List[Deck], rounds: List[Round], standings: List[Standing]):
        self.tournament = tournament
        self.decks = decks
        self.rounds = rounds
        self.standings = standings

    def __str__(self):
        return f"{len(self.decks)} decks"

@dataclass
class MtgMeleePlayerInfo:
    def __init__(self, username: str, player_name: str, result: str, standing: 'Standing', decks: Optional[List['MtgMeleePlayerDeck']] = None):
        self.username = username
        self.player_name = player_name
        self.result = result
        self.standing = standing
        self.decks = decks if decks is not None else []
    def __str__(self):
        return f"round_name : {self.round_name}, match : {self.match}"


@dataclass
class MtgMeleeConstants:
    # URL templates for various pages
    DECK_PAGE = "https://melee.gg/Decklist/View/{deckId}"
    PLAYER_DETAILS_PAGE = "https://melee.gg/Player/GetPlayerDetails?id={playerId}"
    TOURNAMENT_PAGE = "https://melee.gg/Tournament/View/{tournamentId}"
    TOURNAMENT_LIST_PAGE = "https://melee.gg/Decklist/TournamentSearch"
    ROUND_PAGE = "https://melee.gg/Standing/GetRoundStandings"
    # Parameters for the Tournament List page
    TOURNAMENT_LIST_PARAMETERS = "draw=1&columns%5B0%5D%5Bdata%5D=ID&columns%5B0%5D%5Bname%5D=ID&columns%5B0%5D%5Bsearchable%5D=false&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=Name&columns%5B1%5D%5Bname%5D=Name&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=StartDate&columns%5B2%5D%5Bname%5D=StartDate&columns%5B2%5D%5Bsearchable%5D=false&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=Status&columns%5B3%5D%5Bname%5D=Status&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=Format&columns%5B4%5D%5Bname%5D=Format&columns%5B4%5D%5Bsearchable%5D=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=OrganizationName&columns%5B5%5D%5Bname%5D=OrganizationName&columns%5B5%5D%5Bsearchable%5D=true&columns%5B5%5D%5Borderable%5D=true&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=Decklists&columns%5B6%5D%5Bname%5D=Decklists&columns%5B6%5D%5Bsearchable%5D=true&columns%5B6%5D%5Borderable%5D=true&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=2&order%5B0%5D%5Bdir%5D=desc&start={offset}&length=25&search%5Bvalue%5D=&search%5Bregex%5D=false&q=&startDate={startDate}T00%3A00%3A00.000Z&endDate={endDate}T23%3A59%3A59.999Z";
    # Parameters for the Round Page
    ROUND_PAGE_PARAMETERS = "draw=1&columns%5B0%5D%5Bdata%5D=Rank&columns%5B0%5D%5Bname%5D=Rank&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=true&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=Player&columns%5B1%5D%5Bname%5D=Player&columns%5B1%5D%5Bsearchable%5D=false&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=Decklists&columns%5B2%5D%5Bname%5D=Decklists&columns%5B2%5D%5Bsearchable%5D=false&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=MatchRecord&columns%5B3%5D%5Bname%5D=MatchRecord&columns%5B3%5D%5Bsearchable%5D=false&columns%5B3%5D%5Borderable%5D=false&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=GameRecord&columns%5B4%5D%5Bname%5D=GameRecord&columns%5B4%5D%5Bsearchable%5D=false&columns%5B4%5D%5Borderable%5D=false&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=Points&columns%5B5%5D%5Bname%5D=Points&columns%5B5%5D%5Bsearchable%5D=true&columns%5B5%5D%5Borderable%5D=true&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=OpponentMatchWinPercentage&columns%5B6%5D%5Bname%5D=OpponentMatchWinPercentage&columns%5B6%5D%5Bsearchable%5D=false&columns%5B6%5D%5Borderable%5D=true&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bdata%5D=TeamGameWinPercentage&columns%5B7%5D%5Bname%5D=TeamGameWinPercentage&columns%5B7%5D%5Bsearchable%5D=false&columns%5B7%5D%5Borderable%5D=true&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B8%5D%5Bdata%5D=OpponentGameWinPercentage&columns%5B8%5D%5Bname%5D=OpponentGameWinPercentage&columns%5B8%5D%5Bsearchable%5D=false&columns%5B8%5D%5Borderable%5D=true&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B9%5D%5Bdata%5D=FinalTiebreaker&columns%5B9%5D%5Bname%5D=FinalTiebreaker&columns%5B9%5D%5Bsearchable%5D=true&columns%5B9%5D%5Borderable%5D=true&columns%5B9%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B9%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B10%5D%5Bdata%5D=OpponentCount&columns%5B10%5D%5Bname%5D=OpponentCount&columns%5B10%5D%5Bsearchable%5D=true&columns%5B10%5D%5Borderable%5D=true&columns%5B10%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B10%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=0&order%5B0%5D%5Bdir%5D=asc&start={start}&length=25&search%5Bvalue%5D=&search%5Bregex%5D=false&roundId={roundId}"
    MaxDaysBeforeTournamentMarkedAsEnded = 5
    @staticmethod
    def format_url(url, **params):
        return url.format(**params)

@dataclass
class MtgMeleeDeckInfo:
    def __init__(self, deck_uri: str, player:str ,format: str, mainboard: List['DeckItem'], sideboard: List['DeckItem'], result: Optional[str] = None, rounds: Optional[List['MtgMeleeRoundInfo']] = None):
        self.deck_uri = deck_uri
        self.player = player
        self.format = format
        self.mainboard = mainboard
        self.sideboard = sideboard
        self.result = result 
        self.rounds = rounds if rounds is not None else []
    def __str__(self):
        return (
            f"MtgMeleeDeckInfo(\n"
            f"  deck_uri='{self.deck_uri}',\n"
            f"  player='{self.player}',\n"
            f"  format='{self.format}',\n"
            f"  mainboard=[{', '.join(str(item) for item in self.mainboard)}],\n"
            f"  sideboard=[{', '.join(str(item) for item in self.sideboard)}],\n"
            f"  result='{self.result}',\n"
            f"  rounds=[{', '.join(str(round_info) for round_info in self.rounds)}]\n"
            f")"
        )

    def __eq__(self, other):
        if not isinstance(other, MtgMeleeDeckInfo):
            return False
        return (
            self.deck_uri == other.deck_uri and
            self.player == other.player and
            self.format == other.format and
            self.mainboard == other.mainboard and
            self.sideboard == other.sideboard and
            self.result == other.result and
            self.rounds == other.rounds
        )
@dataclass
class MtgMeleePlayerDeck:
    def __init__(self, deck_id: str, uri: str, format: str):
        self.id = deck_id
        self.uri = uri
        self.format = format

@dataclass
class MtgMeleeRoundInfo:
    def __init__(self, round_name: str, match: 'RoundItem'):
        self.round_name = round_name
        self.match = match
    def __str__(self):
        return f"round_name : {self.round_name}, match : {self.match}"
    def __eq__(self, other):
        return self.round_name == other.round_name and self.match == other.match

@dataclass
class MtgMeleeTournamentInfo:
    def __init__(self, tournament_id: Optional[int], uri: str, date: datetime, organizer: str, name: str, decklists: Optional[int], formats: Optional[List[str]] = None):
        self.id = tournament_id
        self.uri = uri
        self.date = date
        self.organizer = organizer
        self.name = name
        self.decklists = decklists
        self.formats = formats if formats is not None else []
    def __str__(self):
        return (f"Tournament ID: {self.id}\n"
                f"Name: {self.name}\n"
                f"Organizer: {self.organizer}\n"
                f"Date: {self.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"URI: {self.uri}\n"
                f"Decklists: {self.decklists}\n"
                f"Formats: {', '.join(self.formats)}"
                )
    def __eq__(self, other):
        if not isinstance(other, MtgMeleeTournamentInfo):
            return False
        return (self.id == other.id and self.date == other.date)

@dataclass
class MtgMeleeTournament:
    def __init__(
        self,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        date: Optional[datetime] = None,
        organizer: Optional[str] = None,
        name: Optional[str] = None,
        decklists: Optional[int] = None,
        formats: Optional[List[str]] = None,
        excluded_rounds: Optional[List[str]] = None,
        json_file: Optional[str] = None,
        deck_offset: Optional[int] = None,
        expected_decks: Optional[int] = None,  
        fix_behavior: Optional[str] = None 
    ):
        self.id = id
        self.uri = uri
        self.date = date
        self.organizer = organizer
        self.name = name
        self.decklists = decklists
        self.formats = formats
        self.excluded_rounds = excluded_rounds
        self.json_file = json_file
        self.deck_offset = deck_offset
        self.expected_decks = expected_decks
        self.fix_behavior = fix_behavior
    def __eq__(self, other):
        if not isinstance(other, MtgMeleeTournament):
            return False
        return (self.id == other.id and
                self.uri == other.uri and
                self.date == other.date and
                self.organizer == other.organizer and
                self.name == other.name and
                self.decklists == other.decklists and
                self.formats == other.formats and
                self.excluded_rounds == other.excluded_rounds and
                self.json_file == other.json_file and
                self.deck_offset == other.deck_offset and
                self.expected_decks == other.expected_decks and
                self.fix_behavior == other.fix_behavior)
    def __str__(self):
        return (f"MtgMeleeTournament(id={self.id}, uri={self.uri}, date={self.date}, "
                f"organizer={self.organizer}, name={self.name}, decklists={self.decklists}, "
                f"formats={self.formats}, excluded_rounds={self.excluded_rounds}, "
                f"json_file={self.json_file}, deck_offset={self.deck_offset}, "
                f"expected_decks={self.expected_decks}, fix_behavior={self.fix_behavior})"
                )
class RoundItem:
    def __init__(self, player1: str, player2: str, result: str):
        self.player1 = player1
        self.player2 = player2
        self.result = result
    def __eq__(self, other):
        return (self.player1 == other.player1 and
                self.player2 == other.player2 and
                self.result == other.result)
    def __str__(self):
        return f"player1 : {self.player1}, player2 : {self.player2}, result : {self.result}"
@dataclass
class Round:
    def __init__(self, round_name: str, matches: List[RoundItem]):
        self.round_name = round_name
        self.matches = matches

@dataclass
class CacheItem:
    def __init__(self, tournament: str, decks: List[MtgMeleeDeckInfo], standings: List[dict], rounds: List[Round]):
        self.tournament = tournament
        self.decks = decks
        self.standings = standings
        self.rounds = rounds
