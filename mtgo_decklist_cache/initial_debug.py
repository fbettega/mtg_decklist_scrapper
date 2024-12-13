# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 20:48:21 2024

@author: Francois
"""
import os
import base
# from .MTGODecklistCache_Updater_MtgMelee_Client.MtgMeleeClient import MtgMeleeClient
from tools.MtgMeleeClient import MtgMeleeClient

# Exemple d'URL pour tester
TOURNAMENT_URL = "https://melee.gg/Tournament/View/88897"

def main():
    client = MtgMeleeClient()
    # Test de la méthode get_players
    try:
        players = client.get_deck(uri=TOURNAMENT_URL, players=50)
        print(f"Players found: {len(players)}")
        for player in players[:5]:  # Affiche les 5 premiers joueurs
            print(player)
    except Exception as e:
        print(f"Error during get_players: {e}")

if __name__ == "__main__":
    main()

