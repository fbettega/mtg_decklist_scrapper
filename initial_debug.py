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
from Client.ManatraderClient import *


# tournament manatraders-series-duel commander-august-2024-2024-08-31.json
# tournament manatraders-series-pauper-june-2024-2024-06-30.json
def main():
    try:
        tournament = Tournament(uri="https://www.manatraders.com/tournaments/30/", date=datetime(2022, 8, 31))
        mana_trader_get_tournament_details_data = TournamentList().get_tournament_details(tournament)
        # tournament = TournamentList.DL_tournaments(datetime(2024, 6, 20, tzinfo=timezone.utc),datetime(2024, 7, 5, tzinfo=timezone.utc))
        # mana_trader_get_tournament_details_data = TournamentList().get_tournament_details(tournament[0])
        # MTGO.TournamentLoader.get_tournament_details.return_value = Mock()
        # MTGO.TournamentLoader.get_tournament_details.return_value.rounds = get_bracket(uri)
        # vraiment pas sur
    except Exception as e:
        print(f"Error during get_players: {e}")

if __name__ == "__main__":
    main()

