import pytest
# from  MTGmelee.MtgMeleeClient import *
import pdb
import importlib
from datetime import datetime, timezone
from models.base_model import *
import MTGO.MTGOclient as MTGO

# import MTGmelee.MtgMeleeClient
# # Recharger le module
# importlib.reload(MTGmelee.MtgMeleeClient)
# # Réimporter tous les objets exportés par le module
# from MTGmelee.MtgMeleeClient import *

# pytest .\tests\MtgMelee.py 
# pytest .\tests\

###################################################################################################################
# BracketLoaderTests

def retry_get_tournament_details(tournament, retries=3, delay=5):
    for attempt in range(retries):
        tournament_details = MTGO.TournamentLoader.get_tournament_details(tournament)
        if tournament_details:
            return tournament_details
        time.sleep(delay)  # Attendre un peu avant de réessayer
    raise Exception("Erreur : Impossible de récupérer les détails du tournoi après plusieurs tentatives.")

@pytest.fixture(scope="module")
def bracket_data(request):
    """Fixture pour charger les données de test en fonction de l'URL."""
    if request.param == "league":
        tournament = Tournament()
        tournament.uri = "https://www.mtgo.com/decklist/modern-league-2020-08-045236"
        Data = retry_get_tournament_details(tournament).rounds
        result = {
            "test_data": Data,
            "expected": None,
        }
        return result
    elif request.param == "challenge":
        tournament = Tournament()
        tournament.uri = "https://www.mtgo.com/decklist/legacy-challenge-2022-10-2312488075"
        Data = retry_get_tournament_details(tournament).rounds
        result = {
            "test_data": Data,
            "expected": [
                Round(  
                    round_name="Quarterfinals",
                    matches=[
                        RoundItem(player1="Oceansoul92", player2="Butakov", result="2-1-0"),
                        RoundItem(player1="DNSolver", player2="Iwouldliketorespond", result="2-1-0"),
                        RoundItem(player1="Baku_91", player2="Ozymandias17", result="2-1-0"),
                        RoundItem(player1="Didackith", player2="Eureka22422", result="2-1-0"), 
                    ],
                ),
                Round(
                    round_name="Semifinals",
                    matches=[
                        RoundItem(player1="Baku_91", player2="Didackith", result="2-0-0"),
                        RoundItem(player1="DNSolver", player2="Oceansoul92", result="2-0-0"),
                    ],
                ),
                Round(
                    round_name="Finals",
                    matches=[
                        RoundItem(player1="Baku_91", player2="DNSolver", result="2-1-0"),
                    ],
                ),
            ],
        }
        return result

# Testez pour les deux URLs : Uri_league_BracketLoader_test et Uri_challenge_BracketLoader_test
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_data_present_when_expected(bracket_data):
    """Vérifie que les données de bracket sont présentes lorsque attendues."""
    test_data = bracket_data.get("test_data")
    expected_data = bracket_data.get("expected")
    if expected_data and not test_data:
        pytest.fail(f"Expected bracket data but found none for URI: {uri}")



@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_item_count_is_correct(bracket_data):
    """Vérifie que le nombre d'éléments dans chaque round est correct."""
    test_data = bracket_data.get("test_data")
    if test_data:
        assert len(next(r for r in test_data if r.round_name == "Quarterfinals").matches) == 4
        assert len(next(r for r in test_data if r.round_name == "Semifinals").matches) == 2
        assert len(next(r for r in test_data if r.round_name == "Finals").matches) == 1


@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_have_winning_player(bracket_data):
    """Vérifie que chaque match a un joueur gagnant."""
    test_data = bracket_data.get("test_data")
    if test_data:
        for round_ in test_data:
            for match in round_.matches:
                assert match.player1, "Player1 should not be null or empty."

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_have_losing_player(bracket_data):
    """Vérifie que chaque match a un joueur perdant."""
    test_data = bracket_data.get("test_data")
    if test_data:
        for round_ in test_data:
            for match in round_.matches:
                assert match.player2, "Player2 should not be null or empty."
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_have_result(bracket_data):
    """Vérifie que chaque match a un résultat."""
    test_data = bracket_data.get("test_data")
    if test_data:
        for round_ in test_data:
            for match in round_.matches:
                assert match.result, "Match result should not be null or empty."


@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_data_is_correct(bracket_data):
    """Vérifie que les données des brackets sont correctes."""
    test_data = bracket_data.get("test_data")
    expected_data = bracket_data.get("expected")
    assert test_data == expected_data

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_rounds_should_be_in_correct_order(bracket_data):
    """Vérifie que les rounds sont dans le bon ordre."""
    test_data = bracket_data.get("test_data")
    if test_data:
        assert test_data[0].round_name == "Quarterfinals"
        assert test_data[1].round_name == "Semifinals"
        assert test_data[2].round_name == "Finals"