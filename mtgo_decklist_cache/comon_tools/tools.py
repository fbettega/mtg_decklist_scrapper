# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
from datetime import datetime
from typing import List
import requests
from urllib.parse import quote
from collections import defaultdict


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
            "Goblin": "_____ Goblin",
        })

    @classmethod
    def normalize(cls, card: str) -> str:
        card = card.strip()
        if card.startswith(cls._alchemy_prefix):
            card = card[len(cls._alchemy_prefix):]
        return cls._normalization.get(card, card)

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
        return text.lower().replace(" ", "-")
    
