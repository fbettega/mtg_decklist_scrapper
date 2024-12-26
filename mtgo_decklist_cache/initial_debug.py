# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 20:48:21 2024

@author: Francois
"""
import os
import base
from datetime import datetime
# from .MTGODecklistCache_Updater_MtgMelee_Client.MtgMeleeClient import MtgMeleeClient
from MTGmelee.MtgMeleeClient import *


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
        client = MtgMeleeClient()
        analyzer = MtgMeleeAnalyzer()
        tournament_data = next(t for t in client.get_tournaments(datetime(2024, 8, 12, 0, 0, 0), datetime(2024, 8, 12, 0, 0, 0)) if t.uri == "https://melee.gg/Tournament/View/193242")
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

