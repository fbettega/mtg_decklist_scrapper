# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import MTGmelee.MtgMeleeClient as MtgMeleeClient



# Configuration settings
class MtgMeleeAnalyzerSettings:
    BlacklistedTerms = ["term1", "term2"]  # Ajouter les termes réels
    ValidFormats = ["Format1", "Format2"]
    MinimumPlayers = 50
    MininumPercentageOfDecks = 0.7
    PlayersLoadedForAnalysis = 100
    DecksLoadedForAnalysis = 100

@dataclass
class MtgMeleeTournament:
    uri: str
    date: datetime
    name: str
    json_file: str
    deck_offset: Optional[int] = None
    expected_decks: Optional[int] = None
    fix_behavior: Optional[str] = None
    excluded_rounds: Optional[List[str]] = None

@dataclass
class MtgMeleeTournamentInfo:
    uri: str
    date: datetime
    name: str
    formats: List[str]
    decklists: int
    organizer: str

@dataclass
class MtgMeleePlayerInfo:
    decks: Optional[List[str]]

@dataclass
class MtgMeleeDeckInfo:
    uri: str


class FormatDetector:
    @staticmethod
    def detect(decks):
        # Implémenter la détection du format à partir des decks
        pass




class MtgMeleeAnalyzer:
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

        # Skips small tournaments
        if tournament.decklists < MtgMeleeAnalyzerSettings.MinimumPlayers:
            return None

        client = MtgMeleeClient()
        players = client.get_players(tournament.uri, MtgMeleeAnalyzerSettings.PlayersLoadedForAnalysis)

        # Skips empty tournaments
        if not players:
            return None

        # Skips small tournaments
        if len(players) < MtgMeleeAnalyzerSettings.MinimumPlayers:
            return None

        # Skips "mostly empty" tournaments
        total_players = len(players)
        players_with_decks = sum(1 for p in players if p.decks)
        if players_with_decks < total_players * MtgMeleeAnalyzerSettings.MininumPercentageOfDecks:
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
        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            json_file=self.generate_file_name(tournament, tournament.formats[0], -1)
        )

    def generate_multi_format_tournament(self, tournament: MtgMeleeTournamentInfo, players: List[MtgMeleePlayerInfo], offset: int, expected_decks: int) -> MtgMeleeTournament:
        deck_uris = [
            p.decks[offset].uri for p in players if p.decks and len(p.decks) > offset
        ][:MtgMeleeAnalyzerSettings.DecksLoadedForAnalysis]

        decks = [MtgMeleeClient().get_deck(uri, players, True) for uri in deck_uris]
        format_detected = FormatDetector.detect(decks)

        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            json_file=FilenameGenerator.generate_file_name(
                tournament_id=tournament.uri.split("/")[-1],
                name=tournament.name,
                date=tournament.date,
                format=format_detected,
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
        format_detected = FormatDetector.detect(decks)

        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
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
