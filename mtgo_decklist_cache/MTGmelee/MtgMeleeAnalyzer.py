# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from  comon_tools.tools import *
from models.base_model import (
    MtgMeleePlayerInfo
)
from MTGmelee.MtgMeleeClient import *

# Configuration settings
class MtgMeleeAnalyzerSettings:
    MinimumPlayers = 16
    MininumPercentageOfDecks = 0.5
    ValidFormats = ["Standard", "Modern", "Pioneer", "Legacy", "Vintage", "Pauper"]
    PlayersLoadedForAnalysis = 25
    DecksLoadedForAnalysis = 16
    BlacklistedTerms = ["Team "]

class FormatDetector:
    _vintage_cards = ["Black Lotus", "Mox Emerald", "Mox Jet", "Mox Sapphire", "Mox Ruby", "Mox Pearl"]
    _legacy_cards = ["Tundra", "Underground Sea", "Badlands", "Taiga", "Savannah", "Scrubland", "Volcanic Island", "Bayou", "Plateau", "Tropical Island"]
    _modern_cards = ["Flooded Strand", "Polluted Delta", "Bloodstained Mire", "Wooded Foothills", "Windswept Heath", "Marsh Flats", "Scalding Tarn", "Verdant Catacombs", "Arid Mesa", "Misty Rainforest"]
    _pioneer_cards1 = ["Hallowed Fountain", "Watery Grave", "Blood Crypt", "Stomping Ground", "Temple Garden", "Godless Shrine", "Overgrown Tomb", "Breeding Pool", "Steam Vents", "Sacred Foundry"]
    _pioneer_cards2 = ["Nykthos, Shrine to Nyx", "Savai Triome", "Indatha Triome", "Zagoth Triome", "Ketria Triome", "Raugrin Triome", "Spara's Headquarters", "Raffine's Tower", "Xander's Lounge", "Ziatora's Proving Ground", "Jetmir's Garden"]
    _pauper_cards = ["Lightning Bolt", "Counterspell"]

    @staticmethod
    def detect(decks: List[dict]) -> str:
        if any(c["CardName"] in FormatDetector._vintage_cards for d in decks for c in d["Mainboard"]):
            return "Vintage"
        if any(c["CardName"] in FormatDetector._legacy_cards for d in decks for c in d["Mainboard"]):
            return "Legacy"
        if any(c["CardName"] in FormatDetector._modern_cards for d in decks for c in d["Mainboard"]):
            return "Modern"
        if (any(c["CardName"] in FormatDetector._pioneer_cards1 for d in decks for c in d["Mainboard"]) and
            any(c["CardName"] in FormatDetector._pioneer_cards2 for d in decks for c in d["Mainboard"])):
            return "Pioneer"
        if any(c["CardName"] in FormatDetector._pauper_cards for d in decks for c in d["Mainboard"]):
            return "Pauper"
        return "Standard"





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
