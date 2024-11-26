# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:14:04 2024

@author: Francois
"""

from typing import List, Optional
from datetime import datetime

class MtgMeleeDeckInfo:
    def __init__(self, deck_uri: str, format: str, mainboard: List['DeckItem'], sideboard: List['DeckItem'], rounds: Optional[List['MtgMeleeRoundInfo']] = None):
        self.deck_uri = deck_uri
        self.format = format
        self.mainboard = mainboard
        self.sideboard = sideboard
        self.rounds = rounds if rounds is not None else []

class MtgMeleePlayerDeck:
    def __init__(self, deck_id: str, uri: str, format: str):
        self.id = deck_id
        self.uri = uri
        self.format = format

class MtgMeleePlayerInfo:
    def __init__(self, username: str, player_name: str, result: str, standing: 'Standing', decks: Optional[List['MtgMeleePlayerDeck']] = None):
        self.username = username
        self.player_name = player_name
        self.result = result
        self.standing = standing
        self.decks = decks if decks is not None else []

class MtgMeleeRoundInfo:
    def __init__(self, round_name: str, match: 'RoundItem'):
        self.round_name = round_name
        self.match = match

class MtgMeleeTournamentInfo:
    def __init__(self, tournament_id: Optional[int], uri: str, date: datetime, organizer: str, name: str, decklists: Optional[int], formats: Optional[List[str]] = None):
        self.id = tournament_id
        self.uri = uri
        self.date = date
        self.organizer = organizer
        self.name = name
        self.decklists = decklists
        self.formats = formats if formats is not None else []