import pytest
# from  MTGmelee.MtgMeleeClient import *
# import pdb
# import importlib
from datetime import datetime, timezone
from models.base_model import *
import Client.MTGOclient as MTGO
import time
# import MTGmelee.MtgMeleeClient
# # Recharger le module
# importlib.reload(MTGmelee.MtgMeleeClient)
# # Réimporter tous les objets exportés par le module
# from MTGmelee.MtgMeleeClient import *

# pytest .\tests\test_MTGO.py
# pytest .\tests\

###################################################################################################################
# BracketLoaderTests


def retry_get_tournament_details(tournament, retries=3, delay=2):
    for attempt in range(retries):
        tournament_details = MTGO.TournamentList().get_tournament_details(tournament)
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
        Data = retry_get_tournament_details(tournament)
        result = {
            "Deck":{
                "test_data": Data.decks,
                "expected": {
                "Number_of_deck": 57,
                'Deck':Deck(
            date=datetime(2020, 8, 4, 0, 0, 0, tzinfo=timezone.utc),
            player="Frozon",
            result="5-0",
            anchor_uri="https://www.mtgo.com/decklist/modern-league-2020-08-045236#deck_Frozon",
            mainboard = [
                DeckItem(card_name="Ancient Stirrings", count=4),
                DeckItem(card_name="Animation Module", count=3),
                DeckItem(card_name="Arcbound Ravager", count=4),
                DeckItem(card_name="Arcbound Worker", count=4),
                DeckItem(card_name="Crystalline Giant", count=2),
                DeckItem(card_name="Darksteel Citadel", count=4),
                DeckItem(card_name="Forest", count=8),
                DeckItem(card_name="Hangarback Walker", count=4),
                DeckItem(card_name="Hardened Scales", count=4),
                DeckItem(card_name="Inkmoth Nexus", count=4),
                DeckItem(card_name="Llanowar Reborn", count=2),
                DeckItem(card_name="Metallic Mimic", count=2),
                DeckItem(card_name="Nurturing Peatland", count=2),
                DeckItem(card_name="Pendelhaven", count=1),
                DeckItem(card_name="Phyrexia's Core", count=1),
                DeckItem(card_name="Scrapyard Recombiner", count=2),
                DeckItem(card_name="Steel Overseer", count=2),
                DeckItem(card_name="The Ozolith", count=3),
                DeckItem(card_name="Walking Ballista", count=4),
            ],

            sideboard = [
                DeckItem(card_name="Damping Sphere", count=2),
                DeckItem(card_name="Dismember", count=2),
                DeckItem(card_name="Gemrazer", count=1),
                DeckItem(card_name="Karn, Scion of Urza", count=2),
                DeckItem(card_name="Nature's Claim", count=2),
                DeckItem(card_name="Relic of Progenitus", count=2),
                DeckItem(card_name="Torpor Orb", count=2),
                DeckItem(card_name="Veil of Summer", count=2),
            ]
        )
            }
            },
            "Rounds":{
            "test_data": Data.rounds,
            "expected": None,
            },
        "Standing":{
            "test_data": Data.standings,
            "expected":{
                "count":0,
            "Standing":None
            }
        }
        }
        return result
    elif request.param == "challenge":
        tournament = Tournament()
        tournament.uri = "https://www.mtgo.com/decklist/legacy-challenge-2022-10-2312488075"
        Data = retry_get_tournament_details(tournament)
        result = {
            "Deck":{
                "test_data": Data.decks,
                "expected":{
                "Number_of_deck": 32,
                'Deck':Deck(
            date= datetime(2022, 10, 23, 15, 0, 0, tzinfo=timezone.utc) ,
            player="Baku_91",
            result="1st Place",
            anchor_uri="https://www.mtgo.com/decklist/legacy-challenge-2022-10-2312488075#deck_Baku_91",
            mainboard = [
                DeckItem(card_name="Brainstorm", count=4),
                DeckItem(card_name="Brazen Borrower", count=1),
                DeckItem(card_name="Counterbalance", count=2),
                DeckItem(card_name="Daze", count=3),
                DeckItem(card_name="Delver of Secrets", count=1),
                DeckItem(card_name="Dragon's Rage Channeler", count=4),
                DeckItem(card_name="Expressive Iteration", count=4),
                DeckItem(card_name="Flooded Strand", count=2),
                DeckItem(card_name="Force of Negation", count=1),
                DeckItem(card_name="Force of Will", count=4),
                DeckItem(card_name="Island", count=1),
                DeckItem(card_name="Lightning Bolt", count=4),
                DeckItem(card_name="Mishra's Bauble", count=3),
                DeckItem(card_name="Misty Rainforest", count=2),
                DeckItem(card_name="Murktide Regent", count=4),
                DeckItem(card_name="Mystic Sanctuary", count=1),
                DeckItem(card_name="Polluted Delta", count=2),
                DeckItem(card_name="Ponder", count=4),
                DeckItem(card_name="Pyroblast", count=2),
                DeckItem(card_name="Scalding Tarn", count=2),
                DeckItem(card_name="Steam Vents", count=1),
                DeckItem(card_name="Volcanic Island", count=4),
                DeckItem(card_name="Wasteland", count=4),
            ],
            sideboard = [
                DeckItem(card_name="End the Festivities", count=1),
                DeckItem(card_name="Force of Negation", count=1),
                DeckItem(card_name="Hydroblast", count=1),
                DeckItem(card_name="Meltdown", count=2),
                DeckItem(card_name="Minsc & Boo, Timeless Heroes", count=2),
                DeckItem(card_name="Pyroblast", count=2),
                DeckItem(card_name="Red Elemental Blast", count=1),
                DeckItem(card_name="Submerge", count=2),
                DeckItem(card_name="Surgical Extraction", count=2),
                DeckItem(card_name="Tropical Island", count=1),
            ]
        )
            }},
           "Rounds":{ "test_data": Data.rounds,
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
        },
        "Standing":{
            "test_data": Data.standings,
            "expected":{
                "count":32,
            "Standing":Standing(
                rank = 1,
                player = "Baku_91",
                points = 18,
                omwp = 0.6735,
                gwp = 0.6667,
                ogwp = 0.6047,
                wins = 9,
                losses = 1)
                }
        }
        }
        return result

        
# Testez pour les deux URLs : Uri_league_BracketLoader_test et Uri_challenge_BracketLoader_test
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_data_present_when_expected(bracket_data):
    """Vérifie que les données de bracket sont présentes lorsque attendues."""
    test_data = bracket_data.get("Rounds").get("test_data")
    expected_data = bracket_data.get("Rounds").get("expected")
    if expected_data and not test_data:
        pytest.fail(f"Expected bracket data but found none for URI: {uri}")



@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_item_count_is_correct(bracket_data):
    """Vérifie que le nombre d'éléments dans chaque round est correct."""
    test_data = bracket_data.get("Rounds").get("test_data")
    if test_data:
        assert len(next(r for r in test_data if r.round_name == "Quarterfinals").matches) == 4
        assert len(next(r for r in test_data if r.round_name == "Semifinals").matches) == 2
        assert len(next(r for r in test_data if r.round_name == "Finals").matches) == 1


@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_have_winning_player(bracket_data):
    """Vérifie que chaque match a un joueur gagnant."""
    test_data = bracket_data.get("Rounds").get("test_data")
    if test_data:
        for round_ in test_data:
            for match in round_.matches:
                assert match.player1, "Player1 should not be null or empty."

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_have_losing_player(bracket_data):
    """Vérifie que chaque match a un joueur perdant."""
    test_data = bracket_data.get("Rounds").get("test_data")
    if test_data:
        for round_ in test_data:
            for match in round_.matches:
                assert match.player2, "Player2 should not be null or empty."
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_have_result(bracket_data):
    """Vérifie que chaque match a un résultat."""
    test_data = bracket_data.get("Rounds").get("test_data")
    if test_data:
        for round_ in test_data:
            for match in round_.matches:
                assert match.result, "Match result should not be null or empty."


@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_items_data_is_correct(bracket_data):
    """Vérifie que les données des brackets sont correctes."""
    test_data = bracket_data.get("Rounds").get("test_data")
    expected_data = bracket_data.get("Rounds").get("expected")
    assert test_data == expected_data

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_bracket_rounds_should_be_in_correct_order(bracket_data):
    """Vérifie que les rounds sont dans le bon ordre."""
    test_data = bracket_data.get("Rounds").get("test_data")
    if test_data:
        assert test_data[0].round_name == "Quarterfinals"
        assert test_data[1].round_name == "Semifinals"
        assert test_data[2].round_name == "Finals"

###########################################################################################
# DeckLoaderTests 
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_deck_count_is_correct(bracket_data):
    """Vérifie que le nombre de decks est correct."""
    assert len(bracket_data.get("Deck").get("test_data")) == bracket_data.get("Deck").get("expected").get("Number_of_deck")

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_date(bracket_data):
    """Vérifie que tous les decks ont une date."""
    for deck in bracket_data.get("Deck").get("test_data"):
                assert deck.date == bracket_data.get("Deck").get("expected").get("Deck").date
  
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_players(bracket_data):
    """Vérifie que tous les decks ont des joueurs."""
    for deck in bracket_data.get("Deck").get("test_data"):
        assert deck.player is not None and deck.player != ""
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_mainboards(bracket_data):
    """Vérifie que tous les decks ont un mainboard avec des cartes."""
    for deck in bracket_data.get("Deck").get("test_data"):
        assert len(deck.mainboard) > 0
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_sideboards(bracket_data):
    """Vérifie que tous les decks ont un sideboard avec des cartes."""
    for deck in bracket_data.get("Deck").get("test_data"):
        assert len(deck.sideboard) > 0
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_valid_mainboards(bracket_data):
    """Vérifie que le mainboard de chaque deck contient au moins 60 cartes."""
    for deck in bracket_data.get("Deck").get("test_data"):
        assert sum(item.count for item in deck.mainboard) >= 60
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_valid_sideboards(bracket_data):
    """Vérifie que le sideboard de chaque deck contient au plus 15 cartes."""
    for deck in bracket_data.get("Deck").get("test_data"):
        assert sum(item.count for item in deck.sideboard) <= 15

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_deck_data_is_correct(bracket_data):
    """Vérifie que le premier deck est correct."""
    test_deck = bracket_data.get("Deck").get("test_data")[0]
    assert test_deck == bracket_data.get("Deck").get("expected").get("Deck")

###########################################################################################
# StandingsLoaderTests 
# bracket_data = result 
@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_standings_count_is_correct(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        assert len(test_data) == bracket_data.get("Standing").get("expected").get('count')


@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_standings_have_players(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        for standing in test_data:
            assert standing.player is not None and standing.player != ""

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_standings_have_rank(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        for standing in test_data:
            assert standing.rank > 0

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_standings_have_points(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        assert max(standing.points for standing in test_data) > 0

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_standings_have_omwp(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        assert max(standing.omwp for standing in test_data) > 0

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_gwp(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        assert max(standing.gwp for standing in test_data) > 0

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_decks_have_ogwp(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        assert max(standing.ogwp for standing in test_data) > 0

@pytest.mark.parametrize("bracket_data", ["league", "challenge"], indirect=True)
def test_standing_data_is_correct(bracket_data):
    test_data = bracket_data.get("Standing").get("test_data")
    if test_data:
        test_deck = bracket_data.get("Standing").get("test_data")[0] 
        assert test_deck.player == bracket_data.get("Standing").get("expected").get("Standing").player
        assert test_deck.rank == bracket_data.get("Standing").get("expected").get("Standing").rank
        assert test_deck.points == bracket_data.get("Standing").get("expected").get("Standing").points
        assert test_deck.omwp == bracket_data.get("Standing").get("expected").get("Standing").omwp
        assert test_deck.gwp == bracket_data.get("Standing").get("expected").get("Standing").gwp
        assert test_deck.ogwp == bracket_data.get("Standing").get("expected").get("Standing").ogwp