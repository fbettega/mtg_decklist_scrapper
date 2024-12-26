# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 20:48:21 2024

@author: Francois
"""
import os
import fetch_tournament
from datetime import datetime
# from .MTGODecklistCache_Updater_MtgMelee_Client.MtgMeleeClient import MtgMeleeClient
# from MTGmelee.MtgMeleeClient import *
from models.base_model import *
from comon_tools.tools import *


# try:
#     client = MtgMeleeClient()
#     # players = client.get_players("https://melee.gg/Tournament/View/16429")
#     # deck = client.get_deck("https://melee.gg/Decklist/View/315233", players)
#     # deck_no_rounds = client.get_deck("https://melee.gg/Decklist/View/315233", players, skip_round_data=True)
#     tournament_3 = MtgMeleeTournament(
#         uri="https://melee.gg/Tournament/View/12946",
#          date=datetime(2022, 11, 20, 0, 0, 0)
#          )
#     test_data_round3 = client.get_tournament_details(tournament_3).rounds
# except Exception as e:
#     print(f"An error occurred: {e}")
#     pdb.post_mortem()  # Lance le débogueur en mode post-mortem

def main():
    try:
        decks = [
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fifth", result="1st Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Winner", result="2nd Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Sixth", result="3rd Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Seventh", result="4th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Third", result="5th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Eighth", result="6th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fourth", result="7th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Second", result="8th Place"),
        ]
            
        standings = [
            Standing(player="Fifth", points=10),
            Standing(player="Winner", points=9),
            Standing(player="Sixth", points=8),
            Standing(player="Seventh", points=7),
            Standing(player="Third", points=6),
            Standing(player="Eighth", points=5),
            Standing(player="Fourth", points=4),
            Standing(player="Second", points=3),
        ]

        bracket = [
            Round(
                round_name="Quarterfinals",
                matches=[
                    RoundItem(player1="Winner", player2="Fifth", result="2-0-0"),
                    RoundItem(player1="Second", player2="Sixth", result="2-0-0"),
                    RoundItem(player1="Third", player2="Seventh", result="2-0-0"),
                    RoundItem(player1="Fourth", player2="Eighth", result="2-0-0"),
                ],
            ),
            Round(
                round_name="Semifinals",
                matches=[
                    RoundItem(player1="Winner", player2="Third", result="2-0-0"),
                    RoundItem(player1="Second", player2="Fourth", result="2-0-0"),
                ],
            ),
            Round(
                round_name="Finals",
                matches=[
                    RoundItem(player1="Winner", player2="Second", result="2-0-0")
                ],
            ),
        ]
        expected_decks = [
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Winner", result="1st Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Second", result="2nd Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Third", result="3rd Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fourth", result="4th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fifth", result="5th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Sixth", result="6th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Seventh", result="7th Place"),
            Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Eighth", result="8th Place"),
        ]

        normalized_decks = OrderNormalizer.reorder_decks(decks, standings, bracket, update_result=True)
        # tournament = next(
        # (t for t in client.get_tournaments(datetime(2023, 7, 28, 0, 0),datetime(2023, 7, 28, 0, 0)) if t.id == 16429),
        # None
        # )
        # result = analyzer.get_scraper_tournaments(tournament)[0]
        # players = client.get_players("https://melee.gg/Tournament/View/16429")
        # deck = client.get_deck("https://melee.gg/Decklist/View/315233",players)
        # print(f"Players found: {len(players)}")
        # for player in players[:5]:  # Affiche les 5 premiers joueurs
        #     print(player)
    except Exception as e:
        print(f"Error during get_players: {e}")

if __name__ == "__main__":
    main()

