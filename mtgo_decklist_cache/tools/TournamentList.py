# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:35:32 2024

@author: Francois
"""

import requests
from datetime import datetime, timedelta
from typing import List

# Constants
MTG_MEELE_API_BASE_URL = "https://melee.gg"
MAX_DAYS_BEFORE_TOURNAMENT_MARKED_AS_ENDED = 5

class MtgMeleeClient:
    def get_tournaments(self, start_date: datetime, end_date: datetime) -> List[dict]:
        """Recuperer la liste des tournois pour la période donnée."""
        # Implémentez ici la logique pour interroger l'API de MTG Melee.
        # Exemple (simulation de réponse avec des données factices) :
        response = requests.get(f"{MTG_MEELE_API_BASE_URL}/Tournament/List", params={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat()
        })
        return response.json()

class MtgMeleeAnalyzer:
    def get_scraper_tournaments(self, tournament: dict) -> List[dict]:
        """Analyser les tournois et retourner des informations formatées."""
        # Implémentez ici la logique pour analyser les tournois récupérés.
        return tournament  # Retourne simplement le tournoi tel quel pour l'exemple.

class TournamentList:
    @staticmethod
    def get_tournaments(start_date: datetime, end_date: datetime = None) -> List[dict]:
        """Récupérer les tournois entre les dates start_date et end_date."""
        if start_date < datetime(2020, 1, 1):
            return []  # Si la date de départ est avant le 1er janvier 2020, retourner une liste vide.
        
        if end_date is None:
            end_date = datetime.utcnow()

        result = []

        while start_date < end_date:
            current_end_date = start_date + timedelta(days=7)
            print(f"\r[MtgMelee] Downloading tournaments from {start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}", end="")

            # Créer une instance du client et récupérer les tournois
            client = MtgMeleeClient()
            tournaments = client.get_tournaments(start_date, current_end_date)

            # Analyser les tournois récupérés
            analyzer = MtgMeleeAnalyzer()
            for tournament in tournaments:
                melee_tournaments = analyzer.get_scraper_tournaments(tournament)
                if melee_tournaments:
                    result.extend(melee_tournaments)

            # Passer à la semaine suivante
            start_date = current_end_date

        print("\r[MtgMelee] Download finished".ljust(80))
        return result

# Exemple d'utilisation
# start_date = datetime(2023, 1, 1)
# end_date = datetime(2023, 1, 31)

# tournaments = TournamentList.get_tournaments(start_date, end_date)
# print(f"Found {len(tournaments)} tournaments.")
