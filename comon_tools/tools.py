# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
from datetime import datetime
from typing import List #,Optional
import requests
from urllib.parse import quote
import re
import unicodedata
import json
from collections import defaultdict
from models.base_model import *

class CardNameNormalizer:
    _api_endpoint = "https://api.scryfall.com/cards/search?order=cmc&q={query}"
    _alchemy_prefix = "A-"
    _normalization = {}

    @classmethod
    def initialize(cls):
        cls.add_multiname_cards("is:split", lambda f, b: f"{f} // {b}")
        cls.add_multiname_cards("is:dfc -is:extra", lambda f, b: f"{f}")
        cls.add_multiname_cards("is:adventure", lambda f, b: f"{f}")
        cls.add_multiname_cards("is:flip", lambda f, b: f"{f}")
        cls.add_flavor_names()

        # ManaTraders normalization errors
        cls._normalization.update({
            "Full Art Plains": "Plains",
            "Full Art Island": "Island",
            "Full Art Swamp": "Swamp",
            "Full Art Mountain": "Mountain",
            "Full Art Forest": "Forest",
            # MTGO normalization errors
            "Altar Of Dementia": "Altar of Dementia",
            "Rain Of Tears": "Rain of Tears",
            "\"Name Sticker\" Goblin": "_____ Goblin",
            "Jotun Grunt": "Jötun Grunt",
            "Sol'kanar the Tainted": "Sol'Kanar the Tainted",
            "Furnace Of Rath": "Furnace of Rath",
            # Melee.gg normalization errors
            "\"Magnifying Glass Enthusiast\"": "Jacob Hauken, Inspector",
            "\"Voltaic Visionary\"": "Voltaic Visionary",
            "Goblin": "_____ Goblin"
        })

    @classmethod
    def normalize(cls, card: str) -> str:
            # Retirer les guillemets doubles ou simples autour du nom
        card_strip = card.strip()
        if card_strip.startswith(cls._alchemy_prefix):
            card_strip = card_strip[len(cls._alchemy_prefix):]
        return cls._normalization.get(card_strip, card_strip)

    @classmethod
    def add_multiname_cards(cls, criteria, create_target_name, text_replacement=None, only_combined_names=False):
        api = cls._api_endpoint.replace("{query}", quote(criteria))
        while api:
            response = requests.get(api, headers={"User-Agent": "Mozilla/5.0"})
            data = response.json()
            for card in data.get("data", []):
                if "card_faces" not in card:
                    continue
                front = card["card_faces"][0]["name"]
                back = card["card_faces"][1]["name"]
                if front == back:
                    continue

                if text_replacement:
                    front = text_replacement(front)
                    back = text_replacement(back)

                target = create_target_name(front, back)

                if not only_combined_names:
                    cls._normalization[front] = target
                cls._normalization.update({
                    f"{front}/{back}": target,
                    f"{front} / {back}": target,
                    f"{front}//{back}": target,
                    f"{front} // {back}": target,
                    f"{front}///{back}": target,
                    f"{front} /// {back}": target,
                })
            api = data.get("next_page")

    @classmethod
    def add_flavor_names(cls):
        for query in ["has:flavorname -is:dfc", "has:flavorname is:dfc"]:
            api = cls._api_endpoint.replace("{query}", quote(query))
            while api:
                response = requests.get(api, headers={"User-Agent": "Mozilla/5.0"})
                data = response.json()

                for card in data.get("data", []):
                    if query == "has:flavorname -is:dfc":
                        flavor_name = card.get("flavor_name")
                        if flavor_name:
                            cls._normalization[flavor_name] = card["name"]
                    else:  # DFC flavor names
                        if "card_faces" not in card:
                            continue

                        front = card["card_faces"][0]["name"]
                        back = card["card_faces"][1]["name"]
                        front_flavor = card["card_faces"][0].get("flavor_name")
                        back_flavor = card["card_faces"][1].get("flavor_name")

                        if front_flavor and back_flavor:
                            cls._normalization.update({
                                f"{front_flavor}": front,
                                f"{front_flavor}/{back_flavor}": front,
                                f"{front_flavor} / {back_flavor}": front,
                                f"{front_flavor}//{back_flavor}": front,
                                f"{front_flavor} // {back_flavor}": front,
                                f"{front_flavor}///{back_flavor}": front,
                                f"{front_flavor} /// {back_flavor}": front,
                            })

                api = data.get("next_page")


class FilenameGenerator:
    @staticmethod
    def generate_file_name(tournament_id: str, tournament_name: str, tournament_date: datetime, tournament_format: str, valid_formats: List[str], seat: int) -> str:
        if tournament_format.lower() not in tournament_name.lower():
            tournament_name += f" ({tournament_format})"

        for other_format in [f for f in valid_formats if f.lower() != tournament_format.lower()]:
            if other_format.lower() in tournament_name.lower():
                tournament_name = tournament_name.replace(other_format, other_format[:3], 1)

        if seat >= 0:
            tournament_name += f" (Seat {seat + 1})"

        return f"{SlugGenerator.generate_slug(tournament_name.strip())}-{tournament_id}-{tournament_date.strftime('%Y-%m-%d')}.json"


class DeckNormalizer:
    @staticmethod
    def normalize(deck: Deck) -> Deck:
        deck.mainboard = sorted(
            DeckNormalizer.combine_duplicates(deck.mainboard), 
            key=lambda item: item.card_name
        )
        deck.sideboard = sorted(
            DeckNormalizer.combine_duplicates(deck.sideboard), 
            key=lambda item: item.card_name
        )
        return deck

    @staticmethod
    def combine_duplicates(input_items: List[DeckItem]) -> List[DeckItem]:
        combined = {}
        for item in input_items:
            if item.card_name not in combined:
                combined[item.card_name] = DeckItem(card_name=item.card_name, count=0)
            combined[item.card_name].count += item.count
        return list(combined.values())
    
class SlugGenerator:
    @staticmethod
    def generate_slug(text: str) -> str:
        # Exemple simple : remplacer les espaces par des tirets et mettre en minuscules.
        normalized_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        # Convertir en minuscules
        lowercase_text = normalized_text.lower()
        # Supprimer les caractères non alphanumériques sauf les espaces et tirets
        alphanumeric_text = re.sub(r"[^\w\s-]", "", lowercase_text)
        # Remplacer les espaces et underscores par des tirets
        hyphenated_text = re.sub(r"[\s_]+", "-", alphanumeric_text)
        # Réduire les tirets multiples en un seul
        compacted_text = re.sub(r"-+", "-", hyphenated_text)
        # Supprimer les tirets en début et fin
        slug = compacted_text.strip("-")
        return slug

# a Verifier lourdement
class OrderNormalizer:
    @staticmethod
    def reorder_decks(decks: list[Deck], standings: list[Standing], bracket_rounds: list[Round], update_result: bool) -> list[Deck]:
        ordered_decks = []

        player_order = OrderNormalizer.get_player_order(decks, standings, bracket_rounds)

        position = 1
        for player in player_order:
            deck = next((d for d in decks if d.player == player), None)
            if deck is None:
                position += 1
                continue

            rank = f"{position}th Place"
            if position == 1:
                rank = "1st Place"
            elif position == 2:
                rank = "2nd Place"
            elif position == 3:
                rank = "3rd Place"
            
            position += 1

            if update_result:
                deck.result = rank

            ordered_decks.append(deck)

        return ordered_decks

    @staticmethod
    def get_player_order(decks: list[Deck], standings: list[Standing], bracket_rounds: list[Round]) -> list[str]:
        result = []

        for standing in standings:
            if not hasattr(standing, "rank") or standing.rank is None:
                standing.rank = sum(1 for s in standings if s.points > standing.points) + 1
        # Add players based on standings rank
        for i in range(1, max(s.rank for s in standings) + 1):
            player_name = next((s.player for s in standings if s.rank == i), None)
            if player_name is None:
                result.append("-")
            else:
                result.append(player_name)

        # Adjust order using bracket rounds
        if bracket_rounds is not None:
            for bracket_round in bracket_rounds:
                result = OrderNormalizer.push_to_top(
                    result,
                    [match.player2 for match in bracket_round.matches],
                    standings
                )
                result = OrderNormalizer.push_to_top(
                    result,
                    [match.player1 for match in bracket_round.matches],
                    standings
                )

        # Add missing players from decks
        for deck in decks:
            if deck.player not in result:
                result.append(deck.player)

        return list(dict.fromkeys(result))  # Remove duplicates while preserving order

    @staticmethod
    def push_to_top(players: list[str], pushed_players: list[str], standings: list[Standing]) -> list[str]:
        player_ranks = {
            player: next(s.rank for s in standings if s.player == player)
            for player in pushed_players if any(s.player == player for s in standings)
        }

        remaining_players = [p for p in players if p not in pushed_players]

        # Create the final order: pushed players sorted by rank, followed by remaining players
        result = [p for p, _ in sorted(player_ranks.items(), key=lambda x: x[1])]
        result.extend(remaining_players)

        return result



class moxfieldparser:
    @staticmethod
    def proxy_client(deck_id):
        url_flare_solver = "http://192.168.1.4:8191/v1"
        headers = {"Content-Type": "application/json"}
        data = {
        "cmd": "request.get",
        "url":  f"https://api.moxfield.com/v2/decks/all/{deck_id}",
        "maxTimeout": 60000
        }
        # response = requests.get(url_flare_solver, json=data)
        response = requests.post(url_flare_solver, headers=headers, json=data)
        return response
    def _download_deck(self,url):
        # match = re.search(r'https://moxfield\.com/decks/([a-zA-Z0-9_-]+)', url)
        match = re.search(r'([^/]+)$', url)
        if match:
            deck_id = match.group(1)
            response = self.proxy_client(deck_id)
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                return None  # Retourne None si la réponse ne peut pas être décodée en JSON
            return result
        return None
    
    def parse_result_to_json(self,downloaded_data):
        if not downloaded_data:
            return None
        raw_html = downloaded_data.get("solution").get('response')
        json_match = re.search(r'<pre[^>]*>(.*?)</pre>', raw_html, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)
            try:
                data_dict = json.loads(json_content)
            except json.JSONDecodeError:
                return None  # Retourne None si le JSON est mal formé
            return data_dict
        return None

    def parse_deck(self,url):
        downloaded_data = self._download_deck(url)
        if not downloaded_data:
            return None  # Retourne None si _download_deck retourne None

        json_result = self.parse_result_to_json(downloaded_data)
        if not json_result:
            return None
        
        mainboard = [DeckItem(count=value["quantity"], card_name=key) for key, value in json_result.get("mainboard").items()] 
        sideboard = [
            DeckItem(count=value["quantity"], card_name=key)
            for key, value in list(json_result.get("sideboard", {}).items()) + list(json_result.get("commanders", {}).items())
        ]

        return {"mainboard": mainboard, "sideboard": sideboard}




