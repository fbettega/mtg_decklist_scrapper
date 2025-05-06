# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:39:50 2024

@author: Francois
"""
from datetime import datetime
from typing import List, Optional


class MtgMeleePlayerInfo:
    def __init__(self, username: str, player_name: str, result: str, standing: 'Standing', decks: Optional[List['MtgMeleePlayerDeck']] = None,nb_of_oppo:int = None):
        self.username = username
        self.player_name = player_name
        self.result = result
        self.standing = standing
        self.decks = decks if decks is not None else []
        self.nb_of_oppo = nb_of_oppo if nb_of_oppo is not None else None
    def __str__(self):
        return f"round_name : {self.round_name}, match : {self.match}"
    def to_dict(self):
        return {
            "username": self.username,
            "player_name": self.player_name,
            "result": self.result,
            "standing": self.standing.to_dict() if self.standing else None,
            "decks": [deck.to_dict() for deck in self.decks]
        }

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
    MaxDaysBeforeTournamentMarkedAsEnded = 30
    COOKIE_FILE = "Api_token_and_login/melee_cookies.json"
    CRED_FILE = "Api_token_and_login/melee_login.json"
    LOGIN_URL = "https://melee.gg/Account/SignIn"  
    COOKIE_MAX_AGE_DAYS = 21  # 3 weeks
    # valid decklist treshold
    VALID_DECKLIST_THRESHOLD = 0.5
    Min_number_of_valid_decklists = 5

    @staticmethod
    def format_url(url, **params):
        return url.format(**params)
    @staticmethod
    def build_magic_payload(start_date, end_date, length: int = 50,draw: int = 1,start: int = 0):
    # Convertit en chaîne de caractères format "YYYY-MM-DD"
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        date_filter = f"{start_str}|{end_str}"
        payload = {
                "draw": str(draw),
                "columns[0][data]": "DecklistName",
                "columns[0][name]": "DecklistName",
                "columns[0][searchable]": "true",
                "columns[0][orderable]": "true",
                "columns[0][search][value]": "",
                "columns[0][search][regex]": "false",
                "columns[1][data]": "Game",
                "columns[1][name]": "Game",
                "columns[1][searchable]": "true",
                "columns[1][orderable]": "true",
                "columns[1][search][value]": "MagicTheGathering",
                "columns[1][search][regex]": "false",
                "columns[2][data]": "FormatId",
                "columns[2][name]": "FormatId",
                "columns[2][searchable]": "true",
                "columns[2][orderable]": "false",
                "columns[2][search][value]": "",
                "columns[2][search][regex]": "false",
                "columns[3][data]": "FormatName",
                "columns[3][name]": "FormatName",
                "columns[3][searchable]": "true",
                "columns[3][orderable]": "true",
                "columns[3][search][value]": "",
                "columns[3][search][regex]": "false",
                "columns[4][data]": "OwnerDisplayName",
                "columns[4][name]": "OwnerDisplayName",
                "columns[4][searchable]": "true",
                "columns[4][orderable]": "true",
                "columns[4][search][value]": "",
                "columns[4][search][regex]": "false",
                "columns[5][data]": "TournamentName",
                "columns[5][name]": "TournamentName",
                "columns[5][searchable]": "true",
                "columns[5][orderable]": "true",
                "columns[5][search][value]": "",
                "columns[5][search][regex]": "false",
                "columns[6][data]": "SortDate",
                "columns[6][name]": "SortDate",
                "columns[6][searchable]": "true",
                "columns[6][orderable]": "true",
                "columns[6][data]": "SortDate",
                "columns[6][name]": "SortDate",
                "columns[6][searchable]": "true",
                "columns[6][orderable]": "true",
                "columns[6][search][value]": date_filter,
                "columns[6][search][regex]": "false",
                "columns[7][data]": "TeamRank",
                "columns[7][name]": "TeamRank",
                "columns[7][searchable]": "false",
                "columns[7][orderable]": "true",
                "columns[7][search][value]": "",
                "columns[7][search][regex]": "false",
                "columns[8][data]": "TeamMatchWins",
                "columns[8][name]": "TeamMatchWins",
                "columns[8][searchable]": "false",
                "columns[8][orderable]": "false",
                "columns[8][search][value]": "",
                "columns[8][search][regex]": "false",
                "columns[9][data]": "OrganizationName",
                "columns[9][name]": "OrganizationName",
                "columns[9][searchable]": "true",
                "columns[9][orderable]": "true",
                "columns[9][search][value]": "",
                "columns[9][search][regex]": "false",
                "columns[10][data]": "Records",
                "columns[10][name]": "Records",
                "columns[10][searchable]": "true",
                "columns[10][orderable]": "false",
                "columns[10][search][value]": "",
                "columns[10][search][regex]": "false",
                "columns[11][data]": "Archetypes",
                "columns[11][name]": "Archetypes",
                "columns[11][searchable]": "true",
                "columns[11][orderable]": "false",
                "columns[11][search][value]": "",
                "columns[11][search][regex]": "false",
                "columns[12][data]": "TournamentTags",
                "columns[12][name]": "TournamentTags",
                "columns[12][searchable]": "true",
                "columns[12][orderable]": "false",
                "columns[12][search][value]": "",
                "columns[12][search][regex]": "false",
                "columns[13][data]": "LeaderName",
                "columns[13][name]": "LeaderName",
                "columns[13][searchable]": "true",
                "columns[13][orderable]": "false",
                "columns[13][search][value]": "",
                "columns[13][search][regex]": "false",
                "columns[14][data]": "SecondaryName",
                "columns[14][name]": "SecondaryName",
                "columns[14][searchable]": "true",
                "columns[14][orderable]": "false",
                "columns[14][search][value]": "",
                "columns[14][search][regex]": "false",
                "order[0][column]": "6",
                "order[0][dir]": "desc",
                "start": str(start),
                "length": str(length),
                "search[value]": "",
                "search[regex]": "false"}
        return payload


class MtgMeleeDeckInfo:
    def __init__(self, date: datetime, deck_uri: str, player:str ,format: str, mainboard: List['DeckItem'], sideboard: List['DeckItem'], result: Optional[str] = None, rounds: Optional[List['MtgMeleeRoundInfo']] = None):
        self.date = date
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
            f"  date='{self.date}',\n"
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
            self.date == other.date and
            self.deck_uri == other.deck_uri and
            self.player == other.player and
            self.format == other.format and
            self.mainboard == other.mainboard and
            self.sideboard == other.sideboard and
            self.result == other.result and
            self.rounds == other.rounds
        )
    def to_dict(self):
        return {
            # "Date": self.date.isoformat(),
            "Date": self.date,
            "Player": self.player,
            "Result": self.result,
            "AnchorUri": self.deck_uri,
            # "Format": self.format,
            "Mainboard": [item.to_dict() for item in self.mainboard],  
            "Sideboard": [item.to_dict() for item in self.sideboard],  
            # "rounds": [round_info.to_dict() for round_info in self.rounds]  
        }

class MtgMeleePlayerDeck:
    def __init__(self, deck_id: str, uri: str, format: str,tournament_decklists: Optional['melee_extract_decklist']  =  None):
        self.id = deck_id
        self.uri = uri
        self.format = format,
        self.tournament_decklists = tournament_decklists
    def to_dict(self):
        return {
            "id": self.id,
            "uri": self.uri,
            "format": self.format
        }

class MtgMeleeRoundInfo:
    def __init__(self, round_name: str, match: 'RoundItem'):
        self.round_name = round_name
        self.match = match
    def __str__(self):
        return f"round_name : {self.round_name}, match : {self.match}"
    def __eq__(self, other):
        return self.round_name == other.round_name and self.match == other.match
    def to_dict(self):
        return {
            "round_name": self.round_name,
            "match": self.match.to_dict()  # assuming RoundItem has a to_dict method
        }

class MtgMeleeTournamentInfo:
    def __init__(
            self,
            tournament_id: Optional[int],
            uri: str,
            date: datetime,
            organizer: str, 
            name: str, 
            decklists: Optional[List['melee_extract_decklist']] = None, 
            formats: Optional[List[str]] = None , 
            excluded_rounds: Optional[List[str]] = None,
            statut : Optional[str] = None ):
        self.id = tournament_id
        self.uri = uri
        self.date = date
        self.organizer = organizer
        self.name = name
        self.decklists = decklists if decklists is not None else []
        self.formats = formats if formats is not None else [],
        self.excluded_rounds = excluded_rounds 
        self.statut = statut
    def __str__(self):
        return (f"Tournament ID: {self.id}\n"
                f"Name: {self.name}\n"
                f"Organizer: {self.organizer}\n"
                f"Date: {self.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"URI: {self.uri}\n"
                f"Decklists: {len(self.decklists)} decklists\n"
                f"Formats: {', '.join(self.formats)}"
                )
    def __eq__(self, other):
        if not isinstance(other, MtgMeleeTournamentInfo):
            return False
        return (self.id == other.id and self.date == other.date)
    def to_dict(self):
        return {
            "id": self.id,
            "uri": self.uri,
            "date": self.date,
            "organizer": self.organizer,
            "name": self.name,
            "decklists": [d.to_dict() for d in self.decklists],
            "formats": self.formats
        }

class MtgMeleeTournament:
    def __init__(
        self,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        date: Optional[datetime] = None,
        organizer: Optional[str] = None,
        name: Optional[str] = None,
        decklists:  Optional[List['melee_extract_decklist']] = None, 
        formats: Optional[List[str]] = None,
        excluded_rounds: Optional[List[str]] = None,
        json_file: Optional[str] = None,
        deck_offset: Optional[int] = None,
        expected_decks: Optional[int] = None,  
        fix_behavior: Optional[str] = None ,
    ):
        self.id = id
        self.uri = uri
        self.date = date
        self.organizer = organizer
        self.name = name
        self.decklists = decklists if decklists is not None else []
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
                # self.decklists == other.decklists and
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
    def to_dict(self):
        return {
            # "id": self.id,
            "Date": self.date.isoformat() if self.date else None,
            "Name": self.name,
            "Uri": self.uri,
            # "organizer": self.organizer,
            # "decklists": self.decklists,
            "Formats": self.formats if self.formats else [],
            # "excluded_rounds": self.excluded_rounds if self.excluded_rounds else [],
            # "json_file": self.json_file,
            # "deck_offset": self.deck_offset,
            # "expected_decks": self.expected_decks,
            # "fix_behavior": self.fix_behavior,
        }

class melee_extract_decklist:
    def __init__(
        self,
        uri: Optional[str] = None,
        date: Optional[datetime] = None,
        TournamentId: Optional[int] = None,
        Valid: Optional[bool] = None,
        OwnerDisplayName: Optional[str] = None,
        OwnerUsername: Optional[str] = None,
        Guid: Optional[str] = None,
        DecklistName : Optional[str] = None,
        decklists: Optional[list[dict]] = None,
        decklists_formats: Optional[List[str]] = None
    ):
        self.uri = uri
        self.date = date
        self.TournamentId = TournamentId
        self.Valid = Valid
        self.OwnerDisplayName = OwnerDisplayName
        self.OwnerUsername = OwnerUsername
        self.Guid = Guid
        self.DecklistName = DecklistName
        self.decklists = decklists if decklists is not None else []
        self.decklists_formats = decklists_formats if decklists_formats is not None else []

    def __eq__(self, other):
        if not isinstance(other, melee_extract_decklist):
            return NotImplemented
        return (
            self.uri == other.uri and
            self.date == other.date and
            self.TournamentId == other.TournamentId and
            self.Valid == other.Valid and
            self.OwnerDisplayName == other.OwnerDisplayName and
            self.OwnerUsername == other.OwnerUsername and
            self.Guid == other.Guid and
            self.DecklistName == other.DecklistName and
            self.decklists == other.decklists and
            self.decklists_formats == other.decklists_formats
        )

    def __str__(self):
        return (f"melee_extract_decklist(uri={self.uri}, date={self.date}, "
                f"TournamentId={self.TournamentId}, Valid={self.Valid}, "
                f"OwnerDisplayName={self.OwnerDisplayName}, OwnerUsername={self.OwnerUsername}, "
                f"Guid={self.Guid}, DecklistName={self.DecklistName}, "
                f"decklists={self.decklists}, formats={self.decklists_formats})")

    def to_dict(self):
        return {
            "uri": self.uri,
            "date": self.date.isoformat() if self.date else None,
            "TournamentId": self.TournamentId,
            "Valid": self.Valid,
            "OwnerDisplayName": self.OwnerDisplayName,
            "OwnerUsername": self.OwnerUsername,
            "Guid": self.Guid,
            "DecklistName": self.DecklistName,
            "decklists": self.decklists,
            "formats": self.decklists_formats
        }