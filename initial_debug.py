# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 20:48:21 2024
@author: Francois
"""
import os
import fetch_tournament
from datetime import datetime
# from .MTGODecklistCache_Updater_MtgMelee_Client.MtgMeleeClient import MtgMeleeClient
from Client.MtgMeleeClient import *
from models.base_model import *
from comon_tools.tools import *
# from models.Topdeck_model import *
# from Client.ManatraderClient import *

# manatraders-series-pioneer-april-2023-2023-04-30.json
# tournament manatraders-series-duel commander-august-2024-2024-08-31.json
# tournament manatraders-series-pauper-june-2024-2024-06-30.json

# for t in tournament:
#     print(t)
def main():
    try:
        tournament = TournamentList.DL_tournaments(datetime(2025,2, 14, tzinfo=timezone.utc),datetime(2025, 2, 21, tzinfo=timezone.utc))
        mana_trader_get_tournament_details_data = TournamentList().get_tournament_details(tournament[0])

        # Exemple tournoi insoluble
        # tournament = TournamentList.DL_tournaments(datetime(2023,7, 20, tzinfo=timezone.utc),datetime(2023, 8, 5, tzinfo=timezone.utc))
        # mana_trader_get_tournament_details_data = TournamentList().get_tournament_details(tournament[0])

        # vraiment pas sur
    except Exception as e:
        print(f"Error during get_players: {e}")

if __name__ == "__main__":
    main()

