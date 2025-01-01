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
from models.Topdeck_model import *
from Client.TopDeckClient import *

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
        get_test_data = TournamentList().get_tournament_details(
            Tournament(
                name="The Island Vacation",
                date= datetime(2024, 12, 7, 0, 0, 0, tzinfo=timezone.utc),
                uri="https://topdeck.gg/event/z97Wwe0sadHGT2ymc5Ss"
        )
        )
        # MTGO.TournamentLoader.get_tournament_details.return_value = Mock()
        # MTGO.TournamentLoader.get_tournament_details.return_value.rounds = get_bracket(uri)
        # vraiment pas sur
    except Exception as e:
        print(f"Error during get_players: {e}")

if __name__ == "__main__":
    main()

