# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 20:48:21 2024

@author: Francois
"""
import os
import base
from datetime import datetime
# from .MTGODecklistCache_Updater_MtgMelee_Client.MtgMeleeClient import MtgMeleeClient
from MTGmelee.MtgMeleeClient import MtgMeleeClient
from MTGmelee.MtgMeleeClient import MtgMeleeTournament

def main():
    client = MtgMeleeClient()
    # Test de la méthode get_players get_deck
    players = client.get_players("https://melee.gg/Tournament/View/8248")
    try:
        deck = client.get_deck("https://melee.gg/Decklist/View/182814", players)
        # players = client.get_players("https://melee.gg/Tournament/View/16429")
        # deck = client.get_deck("https://melee.gg/Decklist/View/315233",players)
        # print(f"Players found: {len(players)}")
        # for player in players[:5]:  # Affiche les 5 premiers joueurs
        #     print(player)
    except Exception as e:
        print(f"Error during get_players: {e}")

if __name__ == "__main__":
    main()

