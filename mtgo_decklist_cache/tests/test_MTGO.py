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
# league
Uri_league_BracketLoader_test = "https://www.mtgo.com/decklist/modern-league-2020-08-045236"
# Challenge
Uri_challenge_BracketLoader_test = "https://www.mtgo.com/decklist/legacy-challenge-2022-10-2312488075"

# Fonction de simulation des brackets
@pytest.fixture(scope="module")
def reference_bracket(uri, Uri_league, Uri_challenge):
    if uri == Uri_league:
        # Retourner les données vides ou nulles pour la ligue
        return []
    elif uri == Uri_challenge:
        # Retourner les données du Challenge
        return [
            {
                "round_name": "Quarterfinals",
                "matches": [
                    {"player1": "Baku_91", "player2": "Ozymandias17", "result": "2-1-0"},
                    {"player1": "Didackith", "player2": "Eureka22422", "result": "2-1-0"},
                    {"player1": "DNSolver", "player2": "Iwouldliketorespond", "result": "2-1-0"},
                    {"player1": "Oceansoul92", "player2": "Butakov", "result": "2-1-0"},
                ],
            },
            {
                "round_name": "Semifinals",
                "matches": [
                    {"player1": "Baku_91", "player2": "Didackith", "result": "2-0-0"},
                    {"player1": "DNSolver", "player2": "Oceansoul92", "result": "2-0-0"},
                ],
            },
            {
                "round_name": "Finals",
                "matches": [
                    {"player1": "Baku_91", "player2": "DNSolver", "result": "2-1-0"},
                ],
            },
        ]

@pytest.fixture(scope="module")
def BracketLoader_test_data(uri_par):
    """Fixture pour charger les données de test une fois selon l'URL."""
    tournament = Tournament()
    tournament.uri = uri_par
    # MTGO.TournamentLoader.get_tournament_details.return_value = Mock()
    # MTGO.TournamentLoader.get_tournament_details.return_value.rounds = get_bracket(uri)
    # vraiment pas sur
    result = MTGO.TournamentLoader.get_tournament_details(tournament)
    #.rounds
    return result

# Testez pour les deux URLs : Uri_league_BracketLoader_test et Uri_challenge_BracketLoader_test
@pytest.mark.parametrize("BracketLoader_test_data", [Uri_league_BracketLoader_test, Uri_challenge_BracketLoader_test], indirect=True)
def test_bracket_data_present_when_expected(BracketLoader_test_data):
    """Vérifie que les données de bracket sont présentes lorsque attendues."""
    if get_bracket(BracketLoader_test_data[0]['round_name']) is not None and BracketLoader_test_data is None:
        pytest.fail("Expected bracket data but found none.")


@pytest.mark.parametrize("BracketLoader_test_data", [Uri_league_BracketLoader_test, Uri_challenge_BracketLoader_test], indirect=True)
def test_bracket_item_count_is_correct(BracketLoader_test_data):
    """Vérifie que le nombre d'éléments dans chaque round est correct."""
    if BracketLoader_test_data:
        assert len(next(r for r in BracketLoader_test_data if r["round_name"] == "Quarterfinals")["matches"]) == 4
        assert len(next(r for r in BracketLoader_test_data if r["round_name"] == "Semifinals")["matches"]) == 2
        assert len(next(r for r in BracketLoader_test_data if r["round_name"] == "Finals")["matches"]) == 1


@pytest.mark.parametrize("BracketLoader_test_data", [Uri_league_BracketLoader_test, Uri_challenge_BracketLoader_test], indirect=True)
def test_bracket_items_have_winning_player(BracketLoader_test_data):
    """Vérifie que chaque match a un joueur gagnant."""
    if BracketLoader_test_data:
        for round_ in BracketLoader_test_data:
            for match in round_["matches"]:
                assert match["player1"], "Player1 should not be null or empty."


@pytest.mark.parametrize("BracketLoader_test_data", [Uri_league_BracketLoader_test, Uri_challenge_BracketLoader_test], indirect=True)
def test_bracket_items_have_losing_player(BracketLoader_test_data):
    """Vérifie que chaque match a un joueur perdant."""
    if BracketLoader_test_data:
        for round_ in BracketLoader_test_data:
            for match in round_["matches"]:
                assert match["player2"], "Player2 should not be null or empty."


@pytest.mark.parametrize("BracketLoader_test_data", [Uri_league_BracketLoader_test, Uri_challenge_BracketLoader_test], indirect=True)
def test_bracket_items_have_result(BracketLoader_test_data):
    """Vérifie que chaque match a un résultat."""
    if BracketLoader_test_data:
        for round_ in BracketLoader_test_data:
            for match in round_["matches"]:
                assert match["result"], "Match result should not be null or empty."


@pytest.mark.parametrize("BracketLoader_test_data", [Uri_league_BracketLoader_test, Uri_challenge_BracketLoader_test], indirect=True)
def test_bracket_items_data_is_correct(BracketLoader_test_data):
    """Vérifie que les données des brackets sont correctes."""
    if BracketLoader_test_data:
        # Comparaison avec les données attendues en fonction de l'URL
        if BracketLoader_test_data == reference_bracket(Uri = Uri_league_BracketLoader_test,Uri_league = Uri_league_BracketLoader_test,Uri_challenge = Uri_challenge_BracketLoader_test):
            assert BracketLoader_test_data == reference_bracket(Uri = Uri_league_BracketLoader_test,Uri_league = Uri_league_BracketLoader_test,Uri_challenge = Uri_challenge_BracketLoader_test)
        elif BracketLoader_test_data == reference_bracket(Uri = Uri_challenge_BracketLoader_test,Uri_league = Uri_league_BracketLoader_test,Uri_challenge = Uri_challenge_BracketLoader_test):
            assert BracketLoader_test_data == reference_bracket(Uri = Uri_challenge_BracketLoader_test,Uri_league = Uri_league_BracketLoader_test,Uri_challenge = Uri_challenge_BracketLoader_test)


@pytest.mark.parametrize("BracketLoader_test_data", [Uri_league_BracketLoader_test, Uri_challenge_BracketLoader_test], indirect=True)
def test_bracket_rounds_should_be_in_correct_order(BracketLoader_test_data):
    """Vérifie que les rounds sont dans le bon ordre."""
    if BracketLoader_test_data:
        assert BracketLoader_test_data[0]["round_name"] == "Quarterfinals"
        assert BracketLoader_test_data[1]["round_name"] == "Semifinals"
        assert BracketLoader_test_data[2]["round_name"] == "Finals"